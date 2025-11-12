from __future__ import annotations

import json
import shutil
import tempfile
from copy import deepcopy
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from casestudy.app.core.config import get_settings
from casestudy.app.crud.case_crud import (
    delete_case_documents,
    fetch_case_documents,
    fetch_cases,
)
from casestudy.app.models.case import CaseDocument
from casestudy.app.schemas.case import (
    CaseCreatePayload,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseSummary,
)
from casestudy.utils.load import load_case_from_local
from casestudy.utils.save import save_case
if TYPE_CHECKING:
    from casestudy.utils.semantic_extract import (
        configure_paths as configure_semantic_paths,
        sync_case_to_pinecone,
    )


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

    def get_case_detail(self, case_id: str) -> CaseDetailResponse:
        normalized_id = (case_id or "").strip()
        if not normalized_id:
            raise ValueError("case_id không hợp lệ.")

        context = None
        personas: List[Dict[str, Any]] | None = None
        skeleton = None
        source = "mongo"

        try:
            context, personas, skeleton = fetch_case_documents(normalized_id)
        except Exception as exc:  # pragma: no cover - Mongo connection issues
            logger.warning(
                "Không thể lấy case '%s' từ MongoDB: %s", normalized_id, exc, exc_info=True
            )
            context = personas = skeleton = None

        if not any([context, personas, skeleton]):
            context, personas, skeleton = load_case_from_local(normalized_id)
            source = "local"

        if not any([context, personas, skeleton]):
            raise LookupError(f"Case '{normalized_id}' không tồn tại.")

        persona_payload = None
        if personas is not None:
            persona_payload = {
                "case_id": normalized_id,
                "personas": personas or [],
            }

        return CaseDetailResponse(
            case_id=normalized_id,
            context=context,
            skeleton=skeleton,
            personas=persona_payload,
            source=source,
        )

    def create_case(
        self,
        payload: CaseCreatePayload,
        *,
        persist_local: bool = True,
    ) -> CaseCreateResponse:
        case_id = self._resolve_case_id(payload)
        existed_in_mongo = self._case_exists_in_mongo(case_id)
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
        pinecone_stats: Optional[Dict[str, int]] = None
        pinecone_error: Optional[str] = None
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
            pinecone_stats, pinecone_error = self._sync_semantic_memory(
                case_id, force_rebuild=existed_in_mongo
            )
            personas_count = len(saved_personas)
            message = f"Đã lưu case '{case_id}' lên MongoDB."
            if pinecone_stats:
                formatted_stats = ', '.join(f"{label}:{count}" for label, count in pinecone_stats.items())
                message += f" Sync Pinecone thành công ({formatted_stats})."
            elif pinecone_error:
                message += f" Không sync được Pinecone: {pinecone_error}"
            return CaseCreateResponse(
                case_id=case_id,
                personas_count=personas_count,
                message=message,
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

    def delete_case(self, case_id: str) -> int:
        normalized_id = (case_id or "").strip()
        if not normalized_id:
            raise ValueError("case_id không hợp lệ.")

        deleted_docs = delete_case_documents(normalized_id)
        local_dir = self.settings.case_data_dir / normalized_id
        local_removed = False
        if local_dir.exists():
            shutil.rmtree(local_dir, ignore_errors=True)
            local_removed = True

        if deleted_docs == 0 and not local_removed:
            raise LookupError(f"Case '{normalized_id}' không tồn tại trong MongoDB.")

        return deleted_docs

    def _case_exists_in_mongo(self, case_id: str) -> bool:
        normalized_id = (case_id or "").strip()
        if not normalized_id:
            return False
        try:
            context, personas, skeleton = fetch_case_documents(normalized_id)
        except Exception as exc:  # pragma: no cover - Mongo connection issues
            logger.debug(
                "Không kiểm tra được case '%s' trong MongoDB: %s",
                normalized_id,
                exc,
                exc_info=True,
            )
            return False
        return any([context, personas, skeleton])

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

    def _sync_semantic_memory(
        self, case_id: str, *, force_rebuild: bool = False
    ) -> Tuple[Optional[Dict[str, int]], Optional[str]]:
        """
        Sau khi lưu MongoDB thành công, đẩy nội dung case lên Pinecone để phục vụ tìm kiếm ngữ nghĩa.
        """
        settings = get_settings()
        openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        pinecone_key = getattr(settings, "pinecone_api_key", None) or os.getenv("PINECONE_API_KEY")

        if not openai_key:
            warning = "OPENAI_API_KEY chưa cấu hình, bỏ qua Pinecone sync."
            logger.info(warning)
            return None, warning
        if not pinecone_key:
            warning = "PINECONE_API_KEY chưa cấu hình, bỏ qua Pinecone sync."
            logger.info(warning)
            return None, warning

        self._ensure_env_var("OPENAI_API_KEY", openai_key)
        self._ensure_env_var("PINECONE_API_KEY", pinecone_key)
        self._ensure_env_var("PINECONE_ENVIRONMENT", getattr(settings, "pinecone_environment", None))
        try:
            from casestudy.utils.semantic_extract import (
                configure_paths as configure_semantic_paths,
                sync_case_to_pinecone,
            )

            configure_semantic_paths(case_id)
            stats = sync_case_to_pinecone(case_id, force_rebuild=force_rebuild)
            return stats, None
        except Exception as exc:  # pragma: no cover - external dependency
            logger.warning("Không sync Pinecone cho case '%s': %s", case_id, exc, exc_info=True)
            return None, str(exc)

    @staticmethod
    def _ensure_env_var(key: str, value: Optional[str]) -> None:
        if value and not os.getenv(key):
            os.environ[key] = value
