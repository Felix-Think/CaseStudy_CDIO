from __future__ import annotations

import ast
import json
import logging
import re
import time
import unicodedata
from textwrap import dedent
from typing import Any, Dict, List, Optional

import httpx

from casestudy.app.core.config import get_settings
from casestudy.app.schemas.case import CaseDraftRequest, CaseDraftResponse

logger = logging.getLogger(__name__)

CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*_\d{3}$")
SYSTEM_PROMPT = (
    "You are an expert emergency-scenario writer who thinks carefully before responding."
)

STORY_PROMPT_TEMPLATE = """
Viết một đoạn truyện ngắn (400-600 từ) bằng tiếng Việt, giọng kể như người chứng kiến tại hiện trường.
- Mở cảnh: mô tả thời điểm, ánh sáng, mùi, bề mặt để tạo cảm giác nhập vai.
- Diễn biến: nhắc tên nhân vật chính, thể hiện diễn tiến cảm xúc theo từng bước và xen lời thoại tự nhiên.
- Chính sách/quy trình: lồng ghép các yêu cầu an toàn hoặc quy trình bắt buộc.
- Kết thúc: tóm lại cảm giác chung và hướng bàn giao/điểm đóng của tình huống.

Thông tin người dùng:
- Chủ đề: {base_topic}
- Prompt nguồn: {prompt_source}
- Gợi ý bổ sung:
{hint_text}
"""

STRUCTURED_PROMPT_TEMPLATE = """
Ban nhan duoc cau chuyen hien truong duoi day va nhiem vu la chuyen no thanh mot JSON duy nhat.
Chi tra ve JSON, khong binh luan.
Danh sach canon_events phai co it nhat 3 su kien lien tiep (CE1, CE2, CE3, ...), theo dung trinh tu thoi gian.
Moi su kien can du truong id/title/description/success_criteria/npc_appearance/timeout_turn/on_success/on_fail.
success_criteria la danh sach object {description, levels}; levels gom 5 muc diem (5-1) voi descriptor ngan de tham khao cham diem.

Cau chuyen:
---
{story_text}
---

Yeu cau cau truc JSON:
{
  "case_id": "chuoi_khong_dau_gach_duoi_###",
  "topic": "Chu de tong quan",
  "skeleton": {
    "case_id": "trang case_id",
    "title": "Tieu de case giau hinh anh",
    "canon_events": [
      {
        "id": "CE1",
        "title": "Ten su kien mo dau",
        "description": "Tam luoc su kien voi boi canh khoi phat",
        "success_criteria": [
          {
            "description": "Tieu chi quan sat duoc",
            "levels": [
              {"score": 5, "descriptor": "Xuat sac: chu dong, dung quy trinh, khong sai sot."},
              {"score": 4, "descriptor": "Tot: hoan thanh phan lon, con thieu chi tiet nho."},
              {"score": 3, "descriptor": "Dat: dap ung muc co ban, con cham hoac thieu 1-2 buoc."},
              {"score": 2, "descriptor": "Yeu: bo sot buoc quan trong, can ho tro sat sao."},
              {"score": 1, "descriptor": "Khong dat: xu ly sai cach hoac gay them rui ro."}
            ]
          }
        ],
        "npc_appearance": [{"persona_id": "id", "role": "vai tro"}],
        "timeout_turn": 9,
        "on_success": "Dieu tot dep neu xu ly dung",
        "on_fail": "Hau qua neu xu ly sai"
      },
      {
        "id": "CE2",
        "title": "Ten su kien cao trao",
        "description": "Dien bien leo thang va hanh dong xu ly chinh",
        "success_criteria": [
          {
            "description": "Bien phap can dat",
            "levels": [
              {"score": 5, "descriptor": "Xuat sac: xu ly dut diem, phoi hop nhuan nhuyen."},
              {"score": 4, "descriptor": "Tot: hoan thanh phan lon, con thieu vai diem nho."},
              {"score": 3, "descriptor": "Dat: dap ung muc co ban, chua that su on dinh."},
              {"score": 2, "descriptor": "Yeu: thieu nhieu buoc quan trong, phan ung cham."},
              {"score": 1, "descriptor": "Khong dat: gay them rui ro hoac khong phan ung dung cach."}
            ]
          }
        ],
        "npc_appearance": [{"persona_id": "id", "role": "vai tro phu hop"}],
        "timeout_turn": 8,
        "on_success": "Tiep tuc sang CE3 hoac an dinh tinh huong",
        "on_fail": "Phai lap lai xu ly hoac phat sinh rui ro moi"
      },
      {
        "id": "CE3",
        "title": "Ten su kien ket thuc/ban giao",
        "description": "Khep lai cau chuyen va chuan bi ban giao",
        "success_criteria": [
          {
            "description": "Tieu chi ban giao",
            "levels": [
              {"score": 5, "descriptor": "Xuat sac: ban giao gon gang, du lieu day du, thong nhat ke hoach."},
              {"score": 4, "descriptor": "Tot: ban giao gan day du, con vai muc can bo sung."},
              {"score": 3, "descriptor": "Dat: ban giao co ban, thong tin chua that su chi tiet."},
              {"score": 2, "descriptor": "Yeu: bo sot thong tin quan trong, chua thong nhat buoc tiep theo."},
              {"score": 1, "descriptor": "Khong dat: ban giao that bai hoac gay nham lan."}
            ]
          }
        ],
        "npc_appearance": [{"persona_id": "id", "role": "nguoi nhan ban giao"}],
        "timeout_turn": 7,
        "on_success": "Tong ket va ban giao suon se",
        "on_fail": "Can them buoc ho tro cuoi"
      }
    ]
  },
  "context": {
    "case_id": "trang case_id",
    "topic": "Chu de",
    "initial_context": {
      "scene": {"time": "...", "location": "...", "weather": "...", "noise": "..."},
      "index_event": {"summary": "...", "current_state": "...", "who_first_on_scene": "..."},
      "available_resources": {"resource_key": ["Nguon luc"]},
      "available_resources_meta": {"resource_key": {"label": "...", "note": "..."}}
    },
    "constraints": ["Rang buoc thuc te"],
    "policies": ["Chinh sach lien quan"],
    "handover": "Cach ban giao",
    "success_state": "Buc tranh ket thuc"
  },
  "personas": {
    "case_id": "trang case_id",
    "personas": [
      {
        "id": "slug_name",
        "name": "Ten nhan vat",
        "role": "Vai tro",
        "age": 30,
        "gender": "Nam/Nu/Khac",
        "background": "Mo ta ngan ve boi canh",
        "personality": "Dac diem tinh cach",
        "goal": "Dieu ho muon",
        "speech_pattern": "Phong cach giao tiep",
        "emotion_init": "Cam xuc ban dau",
        "emotion_during": ["Dien bien cam xuc"],
        "emotion_end": "Cam xuc ket thuc",
        "voice_tags": ["tag1", "tag2"]
      }
    ]
  }
}

Luu y:
- Trach xuat thong tin tu cau chuyen da cho, suy luan hop ly neu thieu du kien.
- Giu tieng Viet co dau. Khong chen mo ta ngoai JSON.
"""

FALLBACK_EVENTS = [
    ("CE1", "Tiếp nhận ban đầu", "Thu thập tình hình và ưu tiên xử lý."),
    ("CE2", "Xử lý chính", "Tổ chức nguồn lực và đưa ra quyết định."),
    ("CE3", "Đánh giá & bàn giao", "Tổng kết và bàn giao cho đơn vị tiếp theo."),
]

FALLBACK_CONSTRAINTS = [
    "Tuân thủ quy trình an toàn hiện hành.",
    "Ghi nhận diễn biến để báo cáo và bàn giao.",
]

FALLBACK_POLICIES = [
    "Báo cáo cấp trên khi phát sinh rủi ro.",
    "Chủ động xin hỗ trợ khi vượt quá năng lực.",
]

DEFAULT_PERSONA_SEEDS = [
    ("lan", "Lan", "Điều phối viên hiện trường"),
    ("minh", "Minh", "Chuyên gia kỹ thuật"),
    ("hoa", "Hoa", "Nhân sự hỗ trợ/khách hàng"),
    ("quang", "Quang", "Nhân sự hậu cần"),
]

SCORE_LEVELS_DESC = [
    (5, "Hoan thanh xuat sac, chu dong va dung quy trinh."),
    (4, "Hoan thanh phan lon yeu cau, thieu mot vai chi tiet nho."),
    (3, "Dat muc co ban, con cham hoac thieu 1-2 buoc."),
    (2, "Bo sot nhieu buoc quan trong, can nhac nho hoac ho tro sat sao."),
    (1, "Khong dat, xu ly sai cach hoac gay them rui ro."),
]


class CaseDraftService:
    """Generate case drafts using OpenAI, falling back to heuristics when needed."""

    def __init__(self) -> None:
        settings = get_settings()
        self.openai_api_key = (settings.openai_api_key or "").strip()
        self.openai_model = getattr(settings, "openai_model", "gpt-4o-mini")
        default_endpoint = "https://api.openai.com/v1/chat/completions"
        self.openai_endpoint = getattr(settings, "openai_endpoint", default_endpoint).rstrip("/")

    def draft_case(self, request: CaseDraftRequest) -> CaseDraftResponse:
        warnings: List[str] = []

        if self._is_openai_ready():
            openai_payload = self._call_openai(request)
            response = self._build_response(openai_payload, request, source="OpenAI")
            if response:
                return response
            warnings.append("OpenAI không trả về JSON hợp lệ, chuyển sang fallback heuristics.")

        fallback_payload = self._build_fallback_payload(request)
        response = self._build_response(fallback_payload, request, source="heuristic")
        if response:
            if warnings:
                response.warnings.extend(warnings)
            return response
        raise ValueError("Không thể sinh case từ dữ liệu hiện có.")

    # ------------------------------------------------------------------ OpenAI flow

    def _call_openai(self, request: CaseDraftRequest) -> Optional[Dict[str, Any]]:
        story_prompt = self._build_story_prompt(request)
        story_text = self._invoke_openai(story_prompt, temperature=0.65, max_tokens=1800)
        if not story_text:
            return None

        structured_prompt = self._build_structured_prompt(story_text, request)
        structured_text = self._invoke_openai(structured_prompt, temperature=0.2, max_tokens=2000)
        if not structured_text:
            return None

        return self._coerce_json(structured_text)

    def _invoke_openai(self, prompt_text: str, *, temperature: float, max_tokens: int) -> Optional[str]:
        if not self._is_openai_ready():
            return None

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = httpx.post(self.openai_endpoint, headers=headers, json=body, timeout=40)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = (exc.response.text or "").strip()
            logger.error("OpenAI request failed (%s): %s", exc.response.status_code, detail, exc_info=True)
            return None
        except httpx.HTTPError as exc:
            logger.error("OpenAI request error: %s", exc, exc_info=True)
            return None

        try:
            data = response.json()
        except ValueError:
            logger.warning("OpenAI trả về nội dung không phải JSON: %s", response.text[:400])
            return None

        text = self._extract_openai_text(data)
        if not text:
            logger.warning("OpenAI không trả về nội dung văn bản.")
            return None
        return text

    @staticmethod
    def _extract_openai_text(payload: Dict[str, Any]) -> Optional[str]:
        try:
            for choice in payload.get("choices", []):
                message = choice.get("message") or {}
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    parts: List[str] = []
                    for part in content:
                        if isinstance(part, dict):
                            text = part.get("text") or part.get("content")
                            if isinstance(text, str):
                                parts.append(text)
                        elif isinstance(part, str):
                            parts.append(part)
                    if parts:
                        return "".join(parts)
        except AttributeError:
            return None
        return None

    @staticmethod
    def _coerce_json(text: str) -> Optional[Dict[str, Any]]:
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        candidates: List[str] = []
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            candidates.append(cleaned)
            if 0 <= start < end:
                candidates.append(cleaned[start : end + 1])
        else:
            candidates.append(cleaned)

        for candidate in candidates:
            snippet = candidate.strip()
            if not snippet:
                continue
            try:
                return json.loads(snippet)
            except (ValueError, json.JSONDecodeError):
                pass
            try:
                obj = ast.literal_eval(snippet)
            except (ValueError, SyntaxError):
                continue
            if isinstance(obj, dict):
                return obj
        return None

    def _is_openai_ready(self) -> bool:
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY chưa được cấu hình.")
            return False
        return True

    # ------------------------------------------------------------------ Prompt builders

    def _build_story_prompt(self, request: CaseDraftRequest) -> str:
        hint_text = self._format_prompt_hints(request)
        base_topic = request.topic or "(chưa đặt tên)"
        return dedent(STORY_PROMPT_TEMPLATE).format(
            base_topic=base_topic,
            prompt_source=request.prompt or "(trống)",
            hint_text=hint_text or "Không có yêu cầu bổ sung.",
        ).strip()

    def _build_structured_prompt(self, story_text: str, request: CaseDraftRequest) -> str:
        # Avoid Python .format() conflicts with JSON braces by simple string replacement.
        return dedent(STRUCTURED_PROMPT_TEMPLATE).replace("{story_text}", story_text.strip()).strip()

    def _format_prompt_hints(self, request: CaseDraftRequest) -> str:
        lines: List[str] = []
        if request.topic:
            lines.append(f"- Chủ đề: {request.topic}")
        if request.persona_count:
            lines.append(f"- Số nhân vật mong muốn: {request.persona_count}")
        if request.location:
            lines.append(f"- Địa điểm ưu tiên: {request.location}")

        persona_lines: List[str] = []
        if request.personas:
            for persona in request.personas:
                if isinstance(persona, dict):
                    name = persona.get("name") or persona.get("id") or "Nhân vật"
                    role = persona.get("role") or "vai trò chưa rõ"
                    persona_lines.append(f"  • {name} ({role})")
                else:
                    name = getattr(persona, "name", None) or getattr(persona, "id", None)
                    role = getattr(persona, "role", None)
                    if name or role:
                        persona_lines.append(f"  • {name or 'Nhân vật'} ({role or 'vai trò chưa rõ'})")
        if persona_lines:
            lines.append("- Nhân vật gợi ý:\n" + "\n".join(persona_lines))

        return "\n".join(lines) if lines else "Không có yêu cầu bổ sung."

    # ------------------------------------------------------------------ fallback heuristics

    def _build_fallback_payload(self, request: CaseDraftRequest) -> Dict[str, Any]:
        topic = self._extract_topic(request)
        case_id = self._generate_case_id(topic)

        desired = request.persona_count or request.min_personas or 3
        personas = self._extract_personas(request.prompt or "", desired)
        if not personas:
            personas = self._generate_default_personas(topic, desired or 3)

        for persona in personas:
            persona.setdefault("speech_pattern", "Ngắn gọn, rõ ràng, ưu tiên hành động.")
            persona.setdefault("personality", "Hợp tác tốt, giữ bình tĩnh.")
            persona.setdefault("goal", "Hoàn thành nhiệm vụ được giao.")
            persona.setdefault("emotion_init", "Tập trung cao độ.")
            persona.setdefault("emotion_during", ["Theo sát diễn biến và phản ứng kịp thời."])
            persona.setdefault("emotion_end", "Tổng kết kinh nghiệm để bàn giao.")
            persona.setdefault("voice_tags", ["chuyen-nghiep"])

        skeleton = self._build_simple_skeleton(topic, case_id, personas)
        context = self._build_simple_context(topic, case_id, personas, request)

        return {
            "case_id": case_id,
            "topic": topic,
            "skeleton": skeleton,
            "context": context,
            "personas": {"case_id": case_id, "personas": personas},
            "warnings": ["Case sinh từ fallback heuristics."],
        }

    def _build_simple_skeleton(self, topic: str, case_id: str, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        personas_cycle = personas or [{"id": "persona_1", "role": "Nhan su ho tro"}]
        default_criteria = [
            [
                "Xac dinh tinh huong ro rang va uu tien dung.",
                "Chia se thong tin kip thoi cho dieu phoi.",
            ],
            [
                "Ap dung bien phap xu ly an toan va thich hop.",
                "Phoi hop nhuan nhuyen giua cac nhom lien quan.",
            ],
            [
                "Thu thap bang chung/nhat ky va ban giao ro rang.",
                "Thong bao dien bien cuoi cung cho ben nhan.",
            ],
        ]
        events = []
        for index, (event_id, title, description) in enumerate(FALLBACK_EVENTS, start=1):
            criteria = default_criteria[index - 1] if index - 1 < len(default_criteria) else default_criteria[0]
            events.append(
                {
                    "id": event_id,
                    "title": f"{title} - {topic}",
                    "description": description,
                    "success_criteria": self._build_success_criteria(criteria),
                    "npc_appearance": [
                        {"persona_id": p["id"], "role": p.get("role") or "Nhan su ho tro"} for p in personas_cycle
                    ],
                    "timeout_turn": 8 + index,
                    "on_success": "Tinh huong duoc kiem soat, san sang buoc ke tiep.",
                    "on_fail": "Tinh huong keo dai, can bao cao cap tren.",
                }
            )
        return {"case_id": case_id, "title": f"Tinh huong {topic}", "canon_events": events}

    def _build_simple_context(
        self,
        topic: str,
        case_id: str,
        personas: List[Dict[str, Any]],
        request: CaseDraftRequest,
    ) -> Dict[str, Any]:
        first_persona = personas[0] if personas else {"name": "Nhân sự trực", "role": "Điều phối"}
        scene = {
            "time": "Ngay sau khi nhận tín hiệu khẩn",
            "location": request.location or "Tại hiện trường",
            "weather": "Không xác định",
            "noise": "Thông tin rời rạc",
        }
        index_event = {
            "summary": f"Tình huống liên quan đến {topic.lower()} cần xử lý nhanh.",
            "current_state": "Đội phản ứng đang thu thập dữ liệu và điều phối.",
            "who_first_on_scene": first_persona.get("name", "Điều phối viên"),
        }

        resources: Dict[str, List[str]] = {}
        resources_meta: Dict[str, Dict[str, str]] = {}
        for persona in personas:
            key = persona["id"]
            resources[key] = [
                f"Nhân sự: {persona.get('name')}",
                f"Vai trò: {persona.get('role') or 'Hỗ trợ'}",
            ]
            resources_meta[key] = {
                "label": persona.get("role") or persona.get("name", key),
                "note": persona.get("goal") or "",
            }

        return {
            "case_id": case_id,
            "topic": topic,
            "prompt": (request.prompt or "").strip(),
            "initial_context": {
                "scene": scene,
                "index_event": index_event,
                "available_resources": resources or {"resource_1": ["Ghi chú nguồn lực"]},
                "available_resources_meta": resources_meta
                or {"resource_1": {"label": "Nguồn lực chung", "note": "Có thể phân bổ linh hoạt."}},
            },
            "constraints": FALLBACK_CONSTRAINTS[:],
            "policies": FALLBACK_POLICIES[:],
            "handover": "Bàn giao cho đơn vị trực tiếp quản lý sau khi ổn định.",
            "success_state": "Các bên thống nhất phương án tiếp theo, tình huống trong tầm kiểm soát.",
        }

    def _build_response(
        self,
        payload: Optional[Dict[str, Any]],
        request: CaseDraftRequest,
        *,
        source: str,
    ) -> Optional[CaseDraftResponse]:
        if not payload or not isinstance(payload, dict):
            return None

        case_id = self._sanitize_case_id(payload.get("case_id"), request)
        topic = payload.get("topic") or self._extract_topic(request)
        skeleton = payload.get("skeleton")
        context = payload.get("context")
        personas_payload = payload.get("personas")

        if not all([case_id, topic, skeleton, context, personas_payload]):
            return None

        if isinstance(personas_payload, dict):
            personas = personas_payload.get("personas", [])
        elif isinstance(personas_payload, list):
            personas = personas_payload
            personas_payload = {"case_id": case_id, "personas": personas}
        else:
            return None

        if not isinstance(personas, list) or not personas:
            return None

        personas = self._normalise_personas(personas, case_id)
        skeleton = self._normalise_skeleton(skeleton, case_id, personas)
        context = self._normalise_context(context, case_id, topic, personas, request)

        warnings = list(payload.get("warnings", []))
        if source == "OpenAI":
            warnings.append(f"Sinh case bằng OpenAI ({self.openai_model}).")
        else:
            warnings.append("Sử dụng fallback heuristics (không có phản hồi OpenAI).")

        return CaseDraftResponse(
            case_id=case_id,
            topic=topic,
            prompt=request.prompt,
            skeleton=skeleton,
            context=context,
            personas={"case_id": case_id, "personas": personas},
            warnings=warnings,
        )

    def _normalise_personas(self, personas: List[Dict[str, Any]], case_id: str) -> List[Dict[str, Any]]:
        normalised: List[Dict[str, Any]] = []
        for index, item in enumerate(personas, start=1):
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or f"Nhân vật {index}").strip()
            persona_id = item.get("id") or slugify(name, fallback=f"persona_{index}")
            role = item.get("role") or f"Vai trò {index}"
            emotion_during = self._ensure_list(item.get("emotion_during"))
            voice_tags = self._ensure_list(item.get("voice_tags"), separator=",")

            normalised.append(
                {
                    "id": persona_id,
                    "case_id": case_id,
                    "name": name,
                    "role": role,
                    "age": item.get("age"),
                    "gender": item.get("gender"),
                    "background": item.get("background") or item.get("description"),
                    "personality": item.get("personality") or "Tập trung hỗ trợ nhóm.",
                    "goal": item.get("goal") or "Hoàn thành nhiệm vụ được giao.",
                    "speech_pattern": item.get("speech_pattern") or "Ngắn gọn, rõ ràng.",
                    "emotion_init": item.get("emotion_init") or "Bình tĩnh.",
                    "emotion_during": emotion_during or ["Theo sát diễn biến và phản ứng kịp thời."],
                    "emotion_end": item.get("emotion_end") or "Tổng kết kinh nghiệm để bàn giao.",
                    "voice_tags": voice_tags or ["chuyen-nghiep"],
                }
            )
        return normalised

    def _normalise_skeleton(
        self,
        skeleton: Dict[str, Any],
        case_id: str,
        personas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        events = skeleton.get("canon_events") if isinstance(skeleton, dict) else None
        if not isinstance(events, list) or not events:
            events = self._build_simple_skeleton("Tinh huong", case_id, personas)["canon_events"]

        persona_lookup = {p["id"]: p for p in personas}
        normalised_events: List[Dict[str, Any]] = []

        for index, raw in enumerate(events, start=1):
            if not isinstance(raw, dict):
                continue
            event_id = raw.get("id") or f"CE{index}"
            title = raw.get("title") or f"Su kien {index}"
            description = raw.get("description") or title
            success = self._normalise_success_criteria(raw.get("success_criteria"))
            if not success:
                success = self._build_success_criteria(
                    [
                        "Hoan thanh muc tieu chinh.",
                        "Cap nhat kip thoi cho dieu phoi.",
                    ]
                )
            npc_entries = raw.get("npc_appearance") or raw.get("npc") or []
            npc = self._normalise_npc(npc_entries, persona_lookup) or [
                {"persona_id": p["id"], "role": p.get("role") or "Nhan su ho tro"} for p in personas
            ]

            timeout = raw.get("timeout_turn")
            if isinstance(timeout, str):
                digits = re.findall(r"\d+", timeout)
                timeout = int(digits[0]) if digits else None
            if not isinstance(timeout, int):
                timeout = 6 + index

            normalised_events.append(
                {
                    "id": event_id,
                    "case_id": case_id,
                    "title": title,
                    "description": description,
                    "success_criteria": success,
                    "npc_appearance": npc,
                    "timeout_turn": timeout,
                    "on_success": raw.get("on_success")
                    or "Tinh huong duoc kiem soat, san sang buoc ke tiep.",
                    "on_fail": raw.get("on_fail") or "Tinh huong keo dai, can bao cao cap tren.",
                }
            )

        title = skeleton.get("title") if isinstance(skeleton, dict) else None
        return {"case_id": case_id, "title": title or f"Tinh huong {case_id}", "canon_events": normalised_events}

    def _normalise_context(
        self,
        context: Any,
        case_id: str,
        topic: str,
        personas: List[Dict[str, Any]],
        request: CaseDraftRequest,
    ) -> Dict[str, Any]:
        if not isinstance(context, dict):
            context = {}

        context.setdefault("case_id", case_id)
        context.setdefault("topic", topic)
        context.setdefault("prompt", self._normalise_prompt(request.prompt))

        initial_ctx = context.setdefault("initial_context", {})
        scene = initial_ctx.setdefault("scene", {})
        scene.setdefault("time", "Thời gian")
        scene.setdefault("location", request.location or "Địa điểm")
        scene.setdefault("weather", "Thời tiết")
        scene.setdefault("noise", "Ghi chép")

        index_event = initial_ctx.setdefault("index_event", {})
        index_event.setdefault("summary", f"Tình huống liên quan đến {topic.lower()} cần xử lý.")
        index_event.setdefault("current_state", "Thông tin cần bổ sung, đang được cập nhật.")
        index_event.setdefault("who_first_on_scene", personas[0]["name"] if personas else "Tổ phản ứng nhanh")

        resources = initial_ctx.setdefault("available_resources", {})
        resources_meta = initial_ctx.setdefault("available_resources_meta", {})
        if not resources:
            for persona in personas:
                key = persona["id"]
                resources[key] = [
                    f"Nhân sự: {persona['name']}",
                    f"Vai trò: {persona.get('role') or 'Hỗ trợ'}",
                ]
                resources_meta[key] = {
                    "label": persona.get("role") or persona["name"],
                    "note": persona.get("goal") or "",
                }

        context.setdefault(
            "constraints",
            [
                "Tuân thủ quy trình an toàn trong suốt quá trình xử lý.",
                "Ghi chép đầy đủ để phục vụ bàn giao.",
            ],
        )
        context.setdefault(
            "policies",
            [
                "Báo cáo cấp trên khi có biến động bất thường.",
                "Chủ động xin hỗ trợ nếu vượt quá năng lực hiện tại.",
            ],
        )
        context.setdefault("handover", "Bàn giao cho đơn vị trực sau khi hoàn thành mục tiêu.")
        context.setdefault(
            "success_state",
            "Các bên thống nhất kế hoạch tiếp theo và tình huống nằm trong tầm kiểm soát.",
        )
        return context

    @staticmethod
    def _normalise_prompt(prompt: Optional[str]) -> str:
        return (prompt or "").strip()

    def _sanitize_case_id(self, raw_id: Optional[str], request: CaseDraftRequest) -> str:
        if isinstance(raw_id, str) and CASE_ID_PATTERN.fullmatch(raw_id):
            return raw_id
        topic = self._extract_topic(request)
        base = normalize_slug_base(raw_id or topic or "case")
        suffix = int(time.time()) % 1000
        return f"{base}_{suffix:03d}"

    @staticmethod
    def _extract_topic(request: CaseDraftRequest) -> str:
        if request.topic and request.topic.strip():
            return request.topic.strip()
        text = (request.prompt or "").strip()
        if not text:
            return "Tinh huong huan luyen"
        pattern = re.compile(r"(?:chu de|tinh huong|case)\s*(?:ve|lien quan den)?\s+([^.,;]+)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            for delimiter in (" voi ", " gom ", " bao gom ", " va ", " cung "):
                idx = candidate.lower().find(delimiter)
                if idx != -1:
                    candidate = candidate[:idx].strip()
                    break
            if candidate:
                return candidate[:120]
        return text[:120] if text else "Tinh huong huan luyen"

    def _normalise_success_criteria(self, raw: Any) -> List[Dict[str, Any]]:
        entries: List[Any] = []
        if isinstance(raw, list):
            entries = raw
        elif raw is not None:
            entries = [raw]

        criteria: List[Dict[str, Any]] = []
        for entry in entries:
            if isinstance(entry, dict):
                description = (entry.get("description") or entry.get("title") or "").strip()
                levels = self._normalise_score_levels(entry.get("levels"), description or "tieu chi")
                if not description and not any(level.get("descriptor") for level in levels):
                    continue
                criteria.append({"description": description, "levels": levels})
            elif isinstance(entry, str):
                desc = entry.strip()
                if not desc:
                    continue
                criteria.append(self._build_success_criterion(desc))
        return criteria

    def _normalise_score_levels(self, raw_levels: Any, fallback_label: str) -> List[Dict[str, Any]]:
        level_map: Dict[int, str] = {}
        if isinstance(raw_levels, list):
            for entry in raw_levels:
                if not isinstance(entry, dict):
                    continue
                try:
                    score = int(entry.get("score"))
                except (TypeError, ValueError):
                    continue
                descriptor = (entry.get("descriptor") or entry.get("description") or "").strip()
                if descriptor:
                    level_map[score] = descriptor

        levels: List[Dict[str, Any]] = []
        for score, descriptor in SCORE_LEVELS_DESC:
            resolved = level_map.get(score) or descriptor
            levels.append({"score": score, "descriptor": resolved.replace("{criterion}", fallback_label)})
        return levels or self._build_score_levels(fallback_label)

    def _build_success_criteria(self, descriptions: List[str]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for description in descriptions or []:
            if isinstance(description, str) and description.strip():
                items.append(self._build_success_criterion(description))
        return items or [self._build_success_criterion("Hoan thanh muc tieu chinh.")]

    def _build_success_criterion(self, description: str) -> Dict[str, Any]:
        desc = (description or "").strip() or "Tieu chi thanh cong"
        return {"description": desc, "levels": self._build_score_levels(desc)}

    def _build_score_levels(self, criterion_label: str) -> List[Dict[str, Any]]:
        label = (criterion_label or "tieu chi").strip() or "tieu chi"
        return [{"score": score, "descriptor": desc.replace("{criterion}", label)} for score, desc in SCORE_LEVELS_DESC]

    @staticmethod
    def _normalise_npc(
        entries: Any,
        persona_lookup: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        result: List[Dict[str, str]] = []
        if not isinstance(entries, list):
            return result

        for entry in entries:
            if isinstance(entry, dict):
                persona_id = entry.get("persona_id") or entry.get("id")
                role = entry.get("role") or entry.get("title")
            elif isinstance(entry, str):
                parts = entry.split(":")
                persona_id = parts[0].strip()
                role = ":".join(parts[1:]).strip() if len(parts) > 1 else ""
            else:
                continue
            if not persona_id:
                continue
            result.append(
                {
                    "persona_id": persona_id,
                    "role": role or persona_lookup.get(persona_id, {}).get("role") or "Nhân sự hỗ trợ",
                }
            )
        return result

    @staticmethod
    def _ensure_list(value: Any, *, separator: str = "\n") -> List[str]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, str) and item.strip()]
        if isinstance(value, str):
            return [item.strip() for item in re.split(separator, value) if item.strip()]
        return []

    @staticmethod
    def _extract_personas(prompt: str, desired: int) -> List[Dict[str, Any]]:
        if not prompt:
            return []
        text = prompt.strip()
        pattern = re.compile(r"(?:bao\s*gồm|gồm|nhân\s*vật|nhan\s*vat|gom\s*co)\s*([^.:]+)", re.IGNORECASE)
        matches = pattern.findall(text)
        if not matches:
            matches = re.findall(r"bao\s*g[o\'a]m\s*([^.:]+)", text, re.IGNORECASE)

        if not matches:
            return []

        raw_segment = matches[0]
        raw_items = re.split(r"[,\-;/\n]", raw_segment)
        personas: List[Dict[str, Any]] = []

        for raw in raw_items:
            sub_items = re.split(r"\s+và\s+|\s+va\s+|\s+and\s+", raw, flags=re.IGNORECASE)
            for item in sub_items:
                name = CaseDraftService._clean_persona_name(item)
                if not name:
                    continue
                personas.append(
                    {
                        "id": slugify(name, fallback=f"persona_{len(personas)+1}"),
                        "name": name,
                        "role": f"Vai trò của {name}",
                    }
                )

        if desired and len(personas) < desired:
            personas.extend(CaseDraftService._generate_default_personas("case", desired - len(personas)))
        return personas[: desired or len(personas)]

    @staticmethod
    def _clean_persona_name(raw: str) -> Optional[str]:
        cleaned = raw.strip()
        if not cleaned:
            return None
        cleaned = re.sub(
            r"^(?:nh[aâ]n\s*v[aâ]t|bao\s*g[oô]m|g[oô]m|c[oó]|v[oơ]i)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned[:60].strip().title() if cleaned else None

    @staticmethod
    def _generate_default_personas(topic: str, count: int) -> List[Dict[str, Any]]:
        personas: List[Dict[str, Any]] = []
        for index in range(max(count, 3)):
            seed_id, name, role = DEFAULT_PERSONA_SEEDS[index % len(DEFAULT_PERSONA_SEEDS)]
            personas.append(
                {
                    "id": f"{seed_id}_{index+1}",
                    "name": name,
                    "role": role,
                }
            )
        return personas[:count]

    def _generate_case_id(self, topic: str) -> str:
        base = normalize_slug_base(topic or "case")
        suffix = int(time.time()) % 1000
        return f"{base}_{suffix:03d}"


def slugify(value: str, fallback: str) -> str:
    value = value or fallback
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", without_marks).strip("-").lower()
    return slug or fallback


def normalize_slug_base(value: str) -> str:
    base = slugify(value, fallback="case")
    base = re.sub(r"[-_]\d+$", "", base)
    return base or "case"
