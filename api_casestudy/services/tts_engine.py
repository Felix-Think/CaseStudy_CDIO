from __future__ import annotations

import base64
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency guard
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

LOGGER = logging.getLogger(__name__)

_FALSEY = {"0", "no", "false", "disable", "disabled"}


def _env_flag(name: str, default: str = "true") -> bool:
    value = os.getenv(name, default)
    if value is None:
        return default.lower() not in _FALSEY
    return value.strip().lower() not in _FALSEY


def _mime_from_suffix(suffix: str) -> str:
    lookup = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".aac": "audio/aac",
    }
    return lookup.get(suffix.lower(), "audio/wav")


def _suffix_from_mime(mime: str) -> str:
    if not mime:
        return ".wav"
    mime = mime.lower()
    if "mpeg" in mime or "mp3" in mime:
        return ".mp3"
    if "aac" in mime:
        return ".aac"
    return ".wav"


@dataclass
class TTSPayload:
    audio_b64: str
    mime_type: str
    model: str
    voice: str
    text: str


class TTSEngine:
    """
    Thin wrapper around OpenAI TTS streaming API that returns base64 audio payloads.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
        mime_type: str = "audio/wav",
    ) -> None:
        self.enabled = enabled and OpenAI is not None
        self.model = model
        self.voice = voice
        self.mime_type = mime_type or "audio/wav"
        self._client: Optional["OpenAI"] = None

    @classmethod
    def from_env(cls) -> "TTSEngine":
        """
        Build an engine using environment overrides.
        """
        enabled = _env_flag("CASESTUDY_TTS_ENABLED", "true")
        model = os.getenv("CASESTUDY_TTS_MODEL", "gpt-4o-mini-tts")
        voice = os.getenv("CASESTUDY_TTS_VOICE", "alloy")
        mime_type = os.getenv(
            "CASESTUDY_TTS_MIME",
            _mime_from_suffix(os.getenv("CASESTUDY_TTS_SUFFIX", ".wav")),
        )
        return cls(enabled=enabled, model=model, voice=voice, mime_type=mime_type)

    def _ensure_client(self) -> "OpenAI":
        if not self.enabled:
            raise RuntimeError("TTS engine disabled.")
        if OpenAI is None:  # pragma: no cover - guarded above
            raise RuntimeError("OpenAI SDK is unavailable.")
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def synthesize(self, text: Optional[str], *, voice: Optional[str] = None) -> Optional[TTSPayload]:
        """
        Convert facilitator text into a base64 audio payload. Returns None on failure.
        """
        if not self.enabled:
            return None
        cleaned = (text or "").strip()
        if not cleaned:
            return None

        try:
            client = self._ensure_client()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Unable to initialize TTS engine: %s", exc)
            return None

        suffix = _suffix_from_mime(self.mime_type)
        voice_name = (voice or self.voice or "alloy").strip() or "alloy"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            with client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=voice_name,
                input=cleaned,
            ) as response:
                response.stream_to_file(tmp_path)

            audio_bytes = tmp_path.read_bytes()
            audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            return TTSPayload(
                audio_b64=audio_b64,
                mime_type=self.mime_type,
                model=self.model,
                voice=voice_name,
                text=cleaned,
            )
        except Exception as exc:  # pragma: no cover - network/runtime issues
            LOGGER.warning("TTS synthesis failed: %s", exc)
            return None
        finally:
            if tmp_path:
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:  # pragma: no cover - cleanup best effort
                    LOGGER.debug("Unable to remove temp TTS file: %s", tmp_path)
