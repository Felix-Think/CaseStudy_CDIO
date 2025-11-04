from __future__ import annotations

from typing import Dict, Iterable, List

from langchain.docstore.document import Document


def build_semantic_documents(
    context: Dict,
    personas: Iterable[Dict],
    skeleton: Dict,
) -> Dict[str, List[Document]]:
    """
    Quy đổi dữ liệu case thành các nhóm Document phục vụ embedding.
    """
    scene_docs: List[Document] = []
    scene_docs.extend(_build_context_documents(context))
    scene_docs.extend(_build_skeleton_documents(skeleton))

    persona_docs = _build_persona_documents(personas)
    policy_docs = _build_policy_documents(context)

    return {
        "scene": scene_docs,
        "persona": persona_docs,
        "policy": policy_docs,
    }


def _build_context_documents(context: Dict) -> List[Document]:
    initial = context.get("initial_context") or {}
    scene = initial.get("scene") or {}
    index_event = initial.get("index_event") or {}
    resources = initial.get("available_resources") or {}
    constraints = initial.get("constraints") or []
    policies = initial.get("policies_safety_legal") or []

    case_id = context.get("case_id") or "unknown_case"

    resource_lines = []
    for group, items in resources.items():
        rendered_items = ", ".join(items) if isinstance(items, list) else str(items)
        resource_lines.append(f"{group}: {rendered_items}")

    documents = [
        Document(
            page_content=(
                f"Khung cảnh case {case_id}: "
                f"thời gian {scene.get('time', 'không rõ')}, "
                f"thời tiết {scene.get('weather', 'không rõ')}, "
                f"địa điểm {scene.get('location', 'không rõ')}, "
                f"mức ồn {scene.get('noise_level', 'không rõ')}."
            ),
            metadata={"type": "scene", "case_id": case_id},
        ),
        Document(
            page_content=(
                f"Sự kiện ban đầu: {index_event.get('summary', 'N/A')}. "
                f"Tình trạng hiện tại: {index_event.get('current_state', 'N/A')}. "
                f"Người tiếp cận đầu tiên: {index_event.get('who_first_on_scene', 'N/A')}."
            ),
            metadata={"type": "index_event", "case_id": case_id},
        ),
        Document(
            page_content="Nguồn lực sẵn có: " + ("; ".join(resource_lines) or "Chưa rõ."),
            metadata={"type": "available_resources", "case_id": case_id},
        ),
    ]

    if constraints:
        documents.append(
            Document(
                page_content="Ràng buộc hiện trường: " + "; ".join(constraints),
                metadata={"type": "constraints", "case_id": case_id},
            )
        )
    if policies:
        documents.append(
            Document(
                page_content="Chính sách và an toàn: " + "; ".join(policies),
                metadata={"type": "policies", "case_id": case_id},
            )
        )

    success_state = initial.get("success_end_state")
    if success_state:
        documents.append(
            Document(
                page_content=f"Trạng thái thành công mong đợi: {success_state}",
                metadata={"type": "success_end_state", "case_id": case_id},
            )
        )

    return documents


def _build_persona_documents(personas: Iterable[Dict]) -> List[Document]:
    documents: List[Document] = []
    for persona in personas or []:
        case_id = persona.get("case_id") or "unknown_case"
        emotions = list(
            filter(
                None,
                [
                    persona.get("emotion_init"),
                    *(persona.get("emotion_during") or []),
                    persona.get("emotion_end"),
                ],
            )
        )
        voice_tags = persona.get("voice_tags") or []
        voice_tags_str = ", ".join(map(str, voice_tags)) if voice_tags else ""
        page_content = (
            f"Persona {persona.get('id', 'chưa đặt ID')} - {persona.get('name', 'ẩn danh')} "
            f"({persona.get('role', 'vai trò chưa rõ')}). "
            f"Tuổi: {persona.get('age', 'không rõ')}; Giới tính: {persona.get('gender', 'không rõ')}. "
            f"Nền tảng: {persona.get('background', 'không rõ')}. "
            f"Tính cách: {persona.get('personality', 'không rõ')}. "
            f"Mục tiêu: {persona.get('goal', 'không rõ')}. "
            f"Mẫu lời nói: {persona.get('speech_pattern', 'không rõ')}. "
            f"Cảm xúc: {', '.join(emotions) if emotions else 'không rõ'}."
        )
        documents.append(
            Document(
                page_content=page_content,
                metadata={
                    "type": "persona",
                    "case_id": case_id,
                    "persona_id": persona.get("id"),
                    "voice_tags": voice_tags_str,
                },
            )
        )
    return documents


def _build_policy_documents(context: Dict) -> List[Document]:
    documents: List[Document] = []
    initial = context.get("initial_context") or {}
    policies = initial.get("policies_safety_legal") or []
    case_id = context.get("case_id") or "unknown_case"

    for idx, policy in enumerate(policies, start=1):
        if not policy:
            continue
        documents.append(
            Document(
                page_content=str(policy),
                metadata={
                    "type": "policy",
                    "case_id": case_id,
                    "policy_id": f"policy_{idx}",
                },
            )
        )
    return documents


def _build_skeleton_documents(skeleton: Dict) -> List[Document]:
    documents: List[Document] = []
    if not skeleton:
        return documents

    case_id = skeleton.get("case_id") or "unknown_case"
    for event in skeleton.get("canon_events") or []:
        success_criteria = event.get("success_criteria") or []
        npc = event.get("npc_appearance") or []
        npc_rendered = ", ".join(
            f"{item.get('persona_id')} ({item.get('role')})".strip()
            for item in npc
            if item
        )
        page_content = (
            f"Canon Event {event.get('id', 'N/A')}: {event.get('title', 'Không tiêu đề')}. "
            f"Mô tả: {event.get('description', 'Không mô tả')}. "
            f"Tiêu chí thành công: {', '.join(success_criteria) if success_criteria else 'Chưa rõ'}. "
            f"NPC xuất hiện: {npc_rendered or 'Chưa rõ'}. "
            f"Timeout cho phép: {event.get('timeout_turn', 'không rõ')} lượt."
        )
        documents.append(
            Document(
                page_content=page_content,
                metadata={
                    "type": "canon_event",
                    "case_id": case_id,
                    "event_id": event.get("id"),
                },
            )
        )
    return documents
