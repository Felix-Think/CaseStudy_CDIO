"""
Simple microphone-driven STT (Speech-To-Text) and TTS (Text-To-Speech)
workflow built on top of the OpenAI API.

Usage examples:

1) Transcribe 5 seconds of microphone audio:
   python openai_speech.py stt --duration 5

2) Transcribe an existing WAV/MP3 file:
   python openai_speech.py stt --file path/to/audio.wav

3) Convert typed text to speech:
   python openai_speech.py tts --text "Xin chao!"

Set OPENAI_API_KEY in your environment before running this script.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI


SAMPLE_RATE = 16_000
CHANNELS = 1
DTYPE = "float32"

DEFAULT_STT_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "alloy"


def ensure_mono(audio: np.ndarray) -> np.ndarray:
    """Collapse multi-channel audio to mono."""
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1)


def trim_leading_trailing_silence(audio: np.ndarray, threshold_db: float = 35.0) -> np.ndarray:
    """Remove low-energy sections on both ends based on a relative dB threshold."""
    if audio.size == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak == 0:
        return audio
    threshold = peak * (10 ** (-threshold_db / 20.0))
    mask = np.abs(audio) > threshold
    if not np.any(mask):
        return audio
    start = int(np.argmax(mask))
    end = int(len(mask) - np.argmax(mask[::-1]))
    return audio[start:end]


def peak_normalize(audio: np.ndarray, target_peak: float = 0.97) -> np.ndarray:
    """Scale audio so that its absolute peak is close to target_peak."""
    if audio.size == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-6:
        return audio
    scale = target_peak / peak
    normalized = audio * scale
    return np.clip(normalized, -1.0, 1.0)


def preprocess_audio(
    audio: np.ndarray,
    sample_rate: int,
    trim_db: float = 35.0,
    target_peak: float = 0.97,
) -> tuple[np.ndarray, int]:
    """
    Apply simple denoising steps (DC removal, silence trimming, normalization).

    These inexpensive operations usually boost downstream STT accuracy by
    feeding the API cleaner, louder content.
    """
    mono_audio = ensure_mono(np.asarray(audio, dtype=np.float32))
    if mono_audio.size == 0:
        return mono_audio, sample_rate

    centered = mono_audio - float(np.mean(mono_audio))
    trimmed = trim_leading_trailing_silence(centered, trim_db) if trim_db is not None else centered
    if trimmed.size == 0:
        trimmed = centered
    normalized = peak_normalize(trimmed, target_peak)
    if normalized.size == 0:
        normalized = mono_audio
    return normalized.astype(np.float32), sample_rate


_ENV_LOADED = False


def _load_env_file() -> None:
    """Populate os.environ from nearby .env files if present."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    script_dir = Path(__file__).resolve().parent
    search_dirs = [
        script_dir,
        script_dir.parent,
        Path.cwd(),
    ]

    seen = set()
    for directory in search_dirs:
        candidate = (directory / ".env").resolve()
        if candidate in seen or not candidate.exists():
            continue
        seen.add(candidate)
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def require_env_client() -> OpenAI:
    """Create an OpenAI client after validating the API key."""
    _load_env_file()
    api_key = os.getenv("OPENAI_API_KEY1")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Please export it before running this script."
        )
    return OpenAI(api_key=api_key)


def record_microphone(duration: float):
    """Capture mono audio from the default microphone."""
    if duration <= 0:
        raise ValueError("Recording duration must be greater than 0 seconds.")
    total_frames = int(duration * SAMPLE_RATE)
    print(f"[mic] Recording {duration:.1f}s ({total_frames} frames) ...")
    audio = sd.rec(
        total_frames,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
    )
    sd.wait()
    return audio.reshape(-1)


def array_to_wav_buffer(audio, sample_rate: int, *, file_name: str = "microphone.wav") -> io.BytesIO:
    """Serialize a numpy array to a WAV buffer for upload."""
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="wav", subtype="PCM_16")
    buffer.seek(0)
    buffer.name = file_name  # openai expects filename metadata
    return buffer


def resolve_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> Optional[str]:
    """Combine inline prompt text and/or file contents for transcription hints."""
    parts: list[str] = []
    if prompt_file:
        path = Path(prompt_file)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        file_text = path.read_text(encoding="utf-8").strip()
        if file_text:
            parts.append(file_text)
    if prompt:
        inline_text = prompt.strip()
        if inline_text:
            parts.append(inline_text)
    merged = "\n".join(parts).strip()
    return merged or None


def build_transcription_kwargs(args: argparse.Namespace) -> dict[str, object]:
    """Translate CLI arguments into kwargs accepted by the transcription endpoint."""
    kwargs: dict[str, object] = {"model": args.stt_model}
    prompt_text = resolve_prompt(args.prompt, args.prompt_file)
    if prompt_text:
        kwargs["prompt"] = prompt_text
    if args.language:
        kwargs["language"] = args.language
    if args.temperature is not None:
        kwargs["temperature"] = max(0.0, args.temperature)
    return kwargs


def perform_transcription(
    client: OpenAI,
    wav_buffer: io.BytesIO,
    transcription_kwargs: dict[str, object],
) -> str:
    response = client.audio.transcriptions.create(
        file=wav_buffer,
        **transcription_kwargs,
    )
    return (response.text or "").strip()


def transcribe_audio_file(
    client: OpenAI,
    file_path: Path,
    *,
    transcription_kwargs: dict[str, object],
    preprocess: bool = True,
) -> str:
    """Send an audio file to the OpenAI transcription endpoint."""
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    audio, sample_rate = sf.read(file_path, dtype="float32", always_2d=False)
    audio_array = ensure_mono(np.asarray(audio, dtype=np.float32))
    if preprocess:
        audio_array, sample_rate = preprocess_audio(audio_array, sample_rate)
    wav_buffer = array_to_wav_buffer(audio_array, sample_rate, file_name=file_path.name)
    return perform_transcription(client, wav_buffer, transcription_kwargs)


def transcribe_microphone_audio(
    client: OpenAI,
    duration: float,
    *,
    transcription_kwargs: dict[str, object],
    preprocess: bool = True,
) -> str:
    audio = record_microphone(duration)
    processed_audio, sample_rate = preprocess_audio(audio, SAMPLE_RATE) if preprocess else (audio, SAMPLE_RATE)
    wav_buffer = array_to_wav_buffer(processed_audio, sample_rate, file_name="microphone.wav")
    return perform_transcription(client, wav_buffer, transcription_kwargs)


def speak_text(
    client: OpenAI,
    text: str,
    model: str,
    voice: str,
    save_path: Optional[Path] = None,
) -> None:
    """Convert text to speech, play it back, and optionally persist the WAV file."""
    if not text:
        raise ValueError("No text provided for TTS.")

    target_path: Optional[Path] = Path(save_path) if save_path else None
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
    ) as response:
        if target_path is None:
            tmp = tempfile.NamedTemporaryFile(
                prefix="openai-tts-", suffix=".wav", delete=False
            )
            tmp.close()
            target_path = Path(tmp.name)
        response.stream_to_file(target_path)

    data, sr = sf.read(target_path, dtype="float32")
    print(f"[tts] Playing synthesized speech ({len(data)} samples @ {sr} Hz)")
    sd.play(data, sr)
    sd.wait()

    if save_path:
        print(f"[tts] Saved audio to {target_path}")
    else:
        target_path.unlink(missing_ok=True)


def run_stt(args: argparse.Namespace) -> None:
    client = require_env_client()
    transcription_kwargs = build_transcription_kwargs(args)
    preprocess_audio_input = not args.skip_preprocess
    if args.file:
        text = transcribe_audio_file(
            client,
            Path(args.file),
            transcription_kwargs=transcription_kwargs,
            preprocess=preprocess_audio_input,
        )
    else:
        text = transcribe_microphone_audio(
            client,
            args.duration,
            transcription_kwargs=transcription_kwargs,
            preprocess=preprocess_audio_input,
        )

    print("\n=== Transcription ===")
    print(text or "[empty result]")

    if args.auto_tts and text:
        speak_text(
            client,
            text,
            model=args.tts_model,
            voice=args.voice,
            save_path=Path(args.save_audio) if args.save_audio else None,
        )


def read_text_payload(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.text_file:
        path = Path(args.text_file)
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    print("Enter text to synthesize (finish with Ctrl+D / Ctrl+Z):")
    payload = sys.stdin.read().strip()
    if not payload:
        raise ValueError("No text was provided for TTS.")
    return payload


def run_tts(args: argparse.Namespace) -> None:
    client = require_env_client()
    text = read_text_payload(args)
    speak_text(
        client,
        text,
        model=args.tts_model,
        voice=args.voice,
        save_path=Path(args.save_audio) if args.save_audio else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Use OpenAI APIs for speech-to-text (STT) and text-to-speech (TTS).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stt = subparsers.add_parser(
        "stt",
        help="Transcribe microphone input or an audio file with OpenAI.",
    )
    stt.add_argument("--file", type=str, help="Optional path to an audio file to transcribe.")
    stt.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Seconds to record from the microphone when no file is provided.",
    )
    stt.add_argument(
        "--stt-model",
        type=str,
        default=DEFAULT_STT_MODEL,
        help="OpenAI model to use for transcription.",
    )
    stt.add_argument(
        "--language",
        type=str,
        help="Language/locale hint (e.g., 'vi' or 'en-US') to bias the transcription.",
    )
    stt.add_argument(
        "--prompt",
        type=str,
        help="Short inline prompt describing the topic or expected vocabulary.",
    )
    stt.add_argument(
        "--prompt-file",
        type=str,
        help="Path to a text file that contains a longer transcription prompt.",
    )
    stt.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature for the transcription model (try 0.0 for determinism).",
    )
    stt.add_argument(
        "--skip-preprocess",
        action="store_true",
        help="Disable client-side silence trimming and gain normalization.",
    )
    stt.add_argument(
        "--auto-tts",
        action="store_true",
        help="Automatically synthesize the transcription with TTS.",
    )
    stt.add_argument(
        "--tts-model",
        type=str,
        default=DEFAULT_TTS_MODEL,
        help="OpenAI model to use when auto-tts is enabled.",
    )
    stt.add_argument(
        "--voice",
        type=str,
        default=DEFAULT_TTS_VOICE,
        help="Voice to use for the TTS model.",
    )
    stt.add_argument(
        "--save-audio",
        type=str,
        help="Optional path to store synthesized speech when auto-tts is enabled.",
    )
    stt.set_defaults(func=run_stt)

    tts = subparsers.add_parser(
        "tts",
        help="Convert text into OpenAI-based speech playback.",
    )
    tts.add_argument("--text", type=str, help="Text to convert into speech.")
    tts.add_argument(
        "--text-file",
        type=str,
        help="Path to a UTF-8 text file to convert into speech.",
    )
    tts.add_argument(
        "--tts-model",
        type=str,
        default=DEFAULT_TTS_MODEL,
        help="OpenAI model to use for TTS.",
    )
    tts.add_argument(
        "--voice",
        type=str,
        default=DEFAULT_TTS_VOICE,
        help="Voice to use for synthesis.",
    )
    tts.add_argument(
        "--save-audio",
        type=str,
        help="Optional path to store the synthesized speech.",
    )
    tts.set_defaults(func=run_tts)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
