from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_ACCESS_TOKEN = (
    "ya29.a0ATi6K2sdtA1Qegj4HYQHrkEBGMhme1XPXQou47ykHJCAsLdURVwox7zqI7ZUWMMxPOR2KExhcx"
    "Njgd4KIES2CYnxpMa7Gy5GYIvZUI2p182lD3iuJKanbuywxOQg9US7lQaYt5cf-Of8BdP5AzhRdKAi9dI"
    "iqgyjd-qjMCsNG1SOzBOXDrYLc1OuTuZod8khpWVTZVCKddSvM6rAFlqY2rY_x9mtyjp3QN1NycUZqWct"
    "7t40bTwDgwNsBKTiDcaD5F1CB2TzfZDyxwdOTkpBvN6OrFPQiyIZQO0F11h3hYgeWCspsi3KSN3nbXmZO"
    "YU-nAyMuxS3CMUVnD2fvoYMAZb1oMKwwNnjTGUegM2ijS5FaCgYKAT4SARUSFQHGX2MixhlDaFn5RF_A8"
    "DSLROQUlg0371"
)

IMAGE_ENDPOINT = "https://aisandbox-pa.googleapis.com/v1/whisk:generateImage"
DEFAULT_OUTPUT_NAME = "scene_background.jpg"
DEFAULT_SEED = 805022


@dataclass
class BackgroundImageResult:
    case_id: str
    prompt: str
    seed: int
    file_path: Path
    image_bytes: bytes
    source: str


def resolve_access_token(explicit: Optional[str] = None) -> str:
    token = explicit or os.environ.get("GEMINI_ACCESS_TOKEN") or DEFAULT_ACCESS_TOKEN
    if not token:
        raise RuntimeError("Khong tim thay access token cho Gemini image API.")
    return token


def load_scene_payload(base_dir: Path, case_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    context_path = base_dir / case_id / "context.json"
    if not context_path.exists():
        raise FileNotFoundError(f"Khong tim thay context cho case_id '{case_id}' (path: {context_path}).")

    import json

    context = json.loads(context_path.read_text(encoding="utf-8"))
    initial = context.get("initial_context") or {}
    scene = initial.get("scene") or context.get("scene")
    index_event = initial.get("index_event") or context.get("index_event")
    if scene is None and index_event is None:
        raise KeyError("Context khong co truong 'scene' hoac 'index_event'.")
    return scene, index_event


def normalize_scene(scene: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    normalized = {}
    for key in ["time", "weather", "location", "noise_level", "noise"]:
        value = scene.get(key)
        if value:
            normalized_key = "noise_level" if key == "noise" else key
            normalized[normalized_key] = value
    return normalized


def normalize_index_event(index_event: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(index_event, dict):
        return {}
    normalized = {}
    for key in ["summary", "current_state", "who_first_on_scene", "who_first"]:
        value = index_event.get(key)
        if value:
            normalized_key = "who_first_on_scene" if key == "who_first" else key
            normalized[normalized_key] = value
    return normalized


def build_prompt(case_id: str, scene: Optional[Dict[str, Any]], index_event: Optional[Dict[str, Any]] = None) -> str:
    normalized_scene = normalize_scene(scene)
    normalized_index = normalize_index_event(index_event)

    details = []
    labels = {
        "time": "Thoi gian",
        "weather": "Thoi tiet",
        "location": "Dia diem",
        "noise_level": "Khong khi & tieng on",
    }
    for field, label in labels.items():
        value = normalized_scene.get(field)
        if value:
            details.append(f"- {label}: {value}")

    if normalized_index.get("summary"):
        details.append(f"- Tom tat su kien: {normalized_index['summary']}")
    if normalized_index.get("current_state"):
        details.append(f"- Tinh trang nan nhan: {normalized_index['current_state']}")
    if normalized_index.get("who_first_on_scene"):
        details.append(f"- Nguoi tiep can dau tien: {normalized_index['who_first_on_scene']}")

    if not details:
        raise ValueError("Khong co du lieu scene/index_event de sinh prompt.")

    details_text = "\n".join(details)
    return (
        "Tao anh nen chan thuc cho mot ky ban huan luyen cuu ho. "
        "Mo ta boi canh tong quat, tap trung vao moi truong thay vi nhan vat. "
        f"Case ID: {case_id}. Su dung cac chi tiet sau:\n{details_text}\n"
        "Vui long giu mau sac va anh sang phu hop phong cach huan luyen, tranh them nhan vat tao dang."
    )


def request_background_image(access_token: str, prompt: str, seed: int) -> bytes:
    payload = {
        "prompt": prompt,
        "seed": seed,
        "mediaCategory": "MEDIA_CATEGORY_BOARD",
        "imageModelSettings": {
            "imageModel": "IMAGEN_3_5",
            "aspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE",
        },
        "clientContext": {
            "workflowId": "a74cc55c-023d-4356-9657-f294c5fc7476",
            "tool": "BACKBONE",
            "sessionId": ";1762844645888",
        },
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(IMAGE_ENDPOINT, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    encoded = (
        data.get("imagePanels", [{}])[0]
        .get("generatedImages", [{}])[0]
        .get("encodedImage")
    )
    if not encoded:
        raise RuntimeError("Phan hoi khong chua du lieu anh.")
    return base64.b64decode(encoded)


def save_image(base_dir: Path, case_id: str, image_bytes: bytes, file_name: str) -> Path:
    case_dir = base_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    output_path = case_dir / file_name
    output_path.write_bytes(image_bytes)
    return output_path


def generate_background_image(
    *,
    case_id: str,
    base_dir: Path,
    prompt: Optional[str] = None,
    scene: Optional[Dict[str, Any]] = None,
    index_event: Optional[Dict[str, Any]] = None,
    seed: int = DEFAULT_SEED,
    file_name: str = DEFAULT_OUTPUT_NAME,
    access_token: Optional[str] = None,
) -> BackgroundImageResult:
    resolved_prompt = (prompt or "").strip()
    source = "prompt"
    if not resolved_prompt:
        resolved_prompt = build_prompt(case_id, scene, index_event)
        source = "scene"

    token = resolve_access_token(access_token)
    image_bytes = request_background_image(token, resolved_prompt, seed)
    file_path = save_image(base_dir, case_id, image_bytes, file_name)
    return BackgroundImageResult(
        case_id=case_id,
        prompt=resolved_prompt,
        seed=seed,
        file_path=file_path,
        image_bytes=image_bytes,
        source=source,
    )


__all__ = [
    "BackgroundImageResult",
    "DEFAULT_ACCESS_TOKEN",
    "DEFAULT_OUTPUT_NAME",
    "DEFAULT_SEED",
    "build_prompt",
    "generate_background_image",
    "load_scene_payload",
    "request_background_image",
    "resolve_access_token",
    "save_image",
]
