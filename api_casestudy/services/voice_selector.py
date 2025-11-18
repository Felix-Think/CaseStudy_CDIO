from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional


def _slugify(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lower = value.lower()
    try:
        lower = lower.encode("ascii", "ignore").decode("ascii")
    except Exception:
        pass
    slug = re.sub(r"[^a-z0-9]+", "-", lower).strip("-")
    return slug or None


def _load_mapping_from_env() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    raw_map = os.getenv("CASESTUDY_TTS_VOICE_MAP")
    if raw_map:
        try:
            parsed = json.loads(raw_map)
            if isinstance(parsed, dict):
                for key, val in parsed.items():
                    slug = _slugify(str(key))
                    if slug and isinstance(val, str) and val.strip():
                        mapping[slug] = val.strip()
        except json.JSONDecodeError:
            pass

    prefix = "CASESTUDY_TTS_VOICE_"
    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        slug = _slugify(env_key[len(prefix) :])
        if not slug:
            continue
        if env_value and env_value.strip():
            mapping[slug] = env_value.strip()
    return mapping


class VoiceSelector:
    """
    Resolve persona -> voice mapping using environment variables.

    Supports either CASESTUDY_TTS_VOICE_MAP='{"mentor":"alloy"}' or individual
    CASESTUDY_TTS_VOICE_<slug>=voice entries (slug derived from persona id/name).
    """

    def __init__(self, default_voice: Optional[str] = None) -> None:
        self.default_voice = (default_voice or "alloy").strip() or "alloy"
        self.mapping = _load_mapping_from_env()

    @classmethod
    def from_env(cls, default_voice: Optional[str] = None) -> "VoiceSelector":
        return cls(default_voice=default_voice)

    def pick(self, persona_id: Optional[str], speaker: Optional[str]) -> str:
        candidates = [
            _slugify(persona_id),
            _slugify(speaker),
        ]
        for candidate in candidates:
            if candidate and candidate in self.mapping:
                return self.mapping[candidate]
        return self.default_voice
