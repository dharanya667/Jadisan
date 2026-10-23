"""
transcriber.py
Transcribes audio using the local openai-whisper package.

Key behaviours:
  - The Whisper model is loaded ONCE at startup via load_model() and kept in
    memory for the lifetime of the process (no per-request reload).
  - transcribe_audio() accepts a file path (str | Path), not raw bytes.
    main.py saves the downloaded audio to a temp file before calling this.
  - No OpenAI API key is required — everything runs locally.

Model sizes and approximate VRAM/RAM usage:
  tiny   ~39 M params  ~1 GB RAM
  base   ~74 M params  ~1 GB RAM   ← default (good accuracy, fast on CPU)
  small  ~244 M params ~2 GB RAM
  medium ~769 M params ~5 GB RAM
  large  ~1550 M params ~10 GB RAM
"""
import logging
import os
from pathlib import Path
from typing import Optional

import whisper

logger = logging.getLogger(__name__)

# ─── Module-level singleton ───────────────────────────────────────────────────

_model: Optional[whisper.Whisper] = None


def load_model(model_size: str = "small") -> whisper.Whisper:
    """
    Load the Whisper model into memory and cache it as a module-level singleton.
    Call this once at application startup (from main.py lifespan).

    Parameters
    ----------
    model_size : str
        One of: tiny, base, small, medium, large. Defaults to 'base'.
        Can also be overridden via the WHISPER_MODEL env var.
    """
    global _model
    if _model is not None:
        logger.info("Whisper model already loaded — reusing cached instance.")
        return _model

    size = os.getenv("WHISPER_MODEL", model_size)
    logger.info("Loading Whisper model '%s' (this may take a few seconds)…", size)
    _model = whisper.load_model(size)
    logger.info("Whisper model '%s' loaded successfully.", size)
    return _model


def get_model() -> whisper.Whisper:
    """Return the cached model; raises if load_model() was never called."""
    if _model is None:
        raise RuntimeError(
            "Whisper model not initialised. Call load_model() at startup."
        )
    return _model


# ─── Transcription ────────────────────────────────────────────────────────────

async def transcribe_audio(audio_path: str | Path) -> str:
    """
    Transcribe an audio file using the locally loaded Whisper model.

    Parameters
    ----------
    audio_path : str | Path
        Absolute path to the saved audio file (OGG, MP3, WAV, M4A, etc.).
        main.py downloads the Twilio media and saves it to disk before
        calling this function.

    Returns
    -------
    str
        Transcribed text, or empty string if transcription produced nothing.

    Notes
    -----
    - Whisper is CPU-bound; we run it in a thread via asyncio.to_thread()
      so it doesn't block the FastAPI event loop.
    - fp16=False is set explicitly because most CI / demo machines run on CPU
      and PyTorch will warn (or error) if fp16 is requested without a CUDA GPU.
    """
    import asyncio

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    model = get_model()
    logger.info("Transcribing '%s' (size: %d bytes)…", path.name, path.stat().st_size)

    # Run the blocking Whisper call in a thread pool so the event loop is free.
    result = await asyncio.to_thread(
        model.transcribe,
        str(path),
        fp16=False,      # CPU-safe; set True only if CUDA GPU is available
        verbose=False,
    )

    text = result.get("text", "").strip()
    detected_lang = result.get("language", "unknown")
    logger.info(
        "Transcription complete: %d chars | language detected: %s",
        len(text),
        detected_lang,
    )
    return text
