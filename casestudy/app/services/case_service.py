from __future__ import annotations

import json
import shutil
import tempfile
from copy import deepcopy
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from casestudy.app.core.config import get_settings
from casestudy.app.crud.case_crud import fetch_cases
from casestudy.app.models.case import CaseDocument
from casestudy.app.schemas.case import (
    CaseCreatePayload,
    CaseCreateResponse,
    CaseListResponse,
    CaseSummary,
)
from casestudy.utils.load import load_case_from_local
from casestudy.utils.save import save_case


logger = logging.getLogger(__name__)


class CaseService:
    """
    Tầng dịch vụ tập trung toàn bộ nghiệp vụ cho case:
    - Ưu tiên lấy dữ liệu từ MongoDB.
    - Nếu có lỗi kết nối sẽ fallback về dữ liệu local.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def list_cases(self, limit: int = 50) -> CaseListResponse:
        cases, source = self._list_from_mongo(limit)
        if not cases:
            cases, source = self._list_from_local(limit)
        return CaseListResponse(cases=cases, source=source)

    def _list_from_mongo(self, limit: int) -> Tuple[List[CaseSummary], str]:
        try:
            documents = fetch_cases(limit)
        except Exception:
            return [], "local"
        summaries = [self._to_summary(doc) for doc in documents]
        return summaries, "mongo"

    def _list_from_local(self, limit: int) -> Tuple[List[CaseSummary], str]:
        cases_dir: Path = self.settings.case_data_dir
        if not cases_dir.exists():
            return [], "local"

        summaries: List[CaseSummary] = []
        for case_dir in sorted(cases_dir.iterdir()):
            if not case_dir.is_dir():
                continue
            case_id = case_dir.name
            context, _, _ = load_case_from_local(case_id)
            if not context:
                continue
            summaries.append(self._to_summary(CaseDocument.from_dict(context)))
            if len(summaries) >= limit:
                break
        return summaries, "local"

    @staticmethod
    def _to_summary(document: CaseDocument) -> CaseSummary:
        return CaseSummary(
            case_id=document.case_id,
            topic=document.topic,
            summary=document.summary,
            location=document.location,
            time=document.time,
            who_first_on_scene=document.who_first_on_scene,
        )

    def create_case(
        self,
        payload: CaseCreatePayload,
        *,
        persist_local: bool = True,
    ) -> CaseCreateResponse:
        case_id = self._resolve_case_id(payload)
        context = self._prepare_context(case_id, payload.context)
        personas = self._prepare_personas(case_id, payload.personas)
        skeleton = self._prepare_skeleton(case_id, payload.skeleton)

        cleanup_dir = None
        local_path = None

        if persist_local:
            working_dir = self._write_local_case(case_id, context, personas, skeleton)
            local_path = working_dir
        else:
            base_storage = self.settings.case_data_dir
            base_storage.mkdir(parents=True, exist_ok=True)
            temp_path = Path(tempfile.mkdtemp(prefix=f"{case_id}_", dir=str(base_storage)))
            working_dir = self._write_local_case(
                case_id,
                context,
                personas,
                skeleton,
                base_dir=temp_path,
            )
            cleanup_dir = working_dir

        saved_context = saved_personas = saved_skeleton = None
        mongo_error: Exception | None = None
        try:
            saved_context, saved_personas, saved_skeleton = save_case(str(working_dir))
        except Exception as exc:  # pragma: no cover - phụ thuộc MongoDB ngoài hệ thống
            mongo_error = exc
            logger.warning("Không thể lưu case '%s' lên MongoDB: %s", case_id, exc, exc_info=True)

        mongo_succeeded = (
            saved_context is not None and saved_personas is not None and saved_skeleton is not None
        )

        if cleanup_dir and mongo_succeeded:
            shutil.rmtree(cleanup_dir, ignore_errors=True)

        if mongo_succeeded:
            personas_count = len(saved_personas)
            return CaseCreateResponse(
                case_id=case_id,
                personas_count=personas_count,
                message=f"Đã lưu case '{case_id}' lên MongoDB.",
                local_path=str(local_path) if local_path else None,
            )

        # Fallback: giữ dữ liệu local khi MongoDB không khả dụng
        if cleanup_dir and not persist_local:
            local_path = cleanup_dir
        personas_count = len(personas)
        fallback_message = (
            f"Đã lưu case '{case_id}' tại thư mục local."
            + (" Không thể kết nối MongoDB." if mongo_error else "")
        )
        return CaseCreateResponse(
            case_id=case_id,
            personas_count=personas_count,
            message=fallback_message,
            local_path=str(local_path) if local_path else str(working_dir),
        )

    @staticmethod
    def _resolve_case_id(payload: CaseCreatePayload) -> str:
        candidates = [
            payload.case_id,
            payload.context.get("case_id") if isinstance(payload.context, dict) else None,
        ]

        skeleton = payload.skeleton
        if isinstance(skeleton, dict):
            candidates.append(skeleton.get("case_id"))

        personas = payload.personas
        if isinstance(personas, dict):
            candidates.append(personas.get("case_id"))

        for candidate in candidates:
            if candidate:
                return str(candidate)

        raise ValueError("Thiếu case_id trong payload.")

    @staticmethod
    def _prepare_context(case_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        data = deepcopy(context)
        data.pop("_id", None)
        data["case_id"] = case_id
        return data

    @staticmethod
    def _prepare_personas(
        case_id: str, personas_payload: Any
    ) -> List[Dict[str, Any]]:
        if isinstance(personas_payload, dict):
            personas_raw = personas_payload.get("personas", [])
        else:
            personas_raw = personas_payload

        if not isinstance(personas_raw, list):
            raise ValueError("Dữ liệu personas phải là danh sách.")

        personas: List[Dict[str, Any]] = []
        for persona in personas_raw:
            if not isinstance(persona, dict):
                raise ValueError("Mỗi persona phải là object.")
            item = deepcopy(persona)
            item.pop("_id", None)
            item["case_id"] = case_id
            personas.append(item)
        return personas

    @staticmethod
    def _prepare_skeleton(case_id: str, skeleton: Dict[str, Any]) -> Dict[str, Any]:
        data = deepcopy(skeleton)
        data.pop("_id", None)
        data["case_id"] = case_id
        return data

    def _write_local_case(
        self,
        case_id: str,
        context: Dict[str, Any],
        personas: List[Dict[str, Any]],
        skeleton: Dict[str, Any],
        *,
        base_dir: Path | None = None,
    ) -> Path:
        target_dir = base_dir or (self.settings.case_data_dir / case_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        with (target_dir / "context.json").open("w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)

        with (target_dir / "personas.json").open("w", encoding="utf-8") as f:
            json.dump(
                {"case_id": case_id, "personas": personas},
                f,
                ensure_ascii=False,
                indent=2,
            )

        with (target_dir / "skeleton.json").open("w", encoding="utf-8") as f:
            json.dump(skeleton, f, ensure_ascii=False, indent=2)

        return target_dir