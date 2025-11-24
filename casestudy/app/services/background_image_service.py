from __future__ import annotations

import base64
from typing import Optional

from casestudy.app.core.config import get_settings
from casestudy.app.schemas.background import BackgroundImageRequest, BackgroundImageResponse
from casestudy.utils.background_image import (
    DEFAULT_OUTPUT_NAME,
    DEFAULT_SEED,
    BackgroundImageResult,
    generate_background_image,
    load_scene_payload,
)


class BackgroundImageService:
    """
    Service sinh anh nen dua tren prompt/scene va luu chung thu muc case.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_background(self, payload: BackgroundImageRequest) -> BackgroundImageResponse:
        case_id = (payload.case_id or "").strip()
        if not case_id:
            raise ValueError("case_id khong hop le.")

        prompt_input = (payload.prompt or "").strip() or None
        scene_payload = payload.scene
        index_event_payload = payload.index_event
        file_name = (payload.file_name or DEFAULT_OUTPUT_NAME).strip() or DEFAULT_OUTPUT_NAME
        seed = payload.seed or DEFAULT_SEED

        if not prompt_input and not scene_payload:
            if not payload.use_local_context:
                raise ValueError("Vui long cung cap prompt hoac scene/index_event de sinh anh.")
            try:
                scene_payload, index_from_file = load_scene_payload(self.settings.case_data_dir, case_id)
            except FileNotFoundError as exc:
                raise ValueError("Khong tim thay context local de sinh prompt.") from exc
            except KeyError as exc:
                raise ValueError(str(exc)) from exc
            if index_event_payload is None:
                index_event_payload = index_from_file

        result = self._render_image(
            case_id=case_id,
            prompt=prompt_input,
            scene=scene_payload,
            index_event=index_event_payload,
            seed=seed,
            file_name=file_name,
        )

        image_base64 = base64.b64encode(result.image_bytes).decode("ascii")
        source_label = self._resolve_source_label(
            prompt_input=prompt_input,
            supplied_scene=payload.scene,
            used_local=not prompt_input and not payload.scene,
        )
        return BackgroundImageResponse(
            case_id=case_id,
            prompt_used=result.prompt,
            file_path=str(result.file_path),
            file_name=result.file_path.name,
            seed=result.seed,
            source=source_label,
            image_base64=image_base64,
            message=f"Da luu anh nen tai {result.file_path}",
        )

    def _render_image(
        self,
        *,
        case_id: str,
        prompt: Optional[str],
        scene: Optional[dict],
        index_event: Optional[dict],
        seed: int,
        file_name: str,
    ) -> BackgroundImageResult:
        return generate_background_image(
            case_id=case_id,
            base_dir=self.settings.case_data_dir,
            prompt=prompt,
            scene=scene,
            index_event=index_event,
            seed=seed,
            file_name=file_name,
            access_token=self.settings.gemini_api_key,
        )

    @staticmethod
    def _resolve_source_label(
        *,
        prompt_input: Optional[str],
        supplied_scene: Optional[dict],
        used_local: bool,
    ) -> str:
        if prompt_input:
            return "prompt"
        if supplied_scene:
            return "scene"
        if used_local:
            return "case_context"
        return "unknown"
