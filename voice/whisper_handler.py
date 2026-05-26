"""
Whisper handler — subprocess wrapper for whisper.cpp with faster-whisper fallback.

Function:
    transcribe(audio_path) -> str

Auto-detects whisper-cli in PATH (whisper.cpp). Falls back to the
faster-whisper Python package if the CLI isn't available.
"""

import logging
import os
import subprocess
import sys
from typing import Optional

logger = logging.getLogger("voice.whisper")


def _find_whisper_cli() -> Optional[str]:
    """Locate the whisper.cpp CLI binary (whisper-cli) in PATH."""
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["where", "whisper-cli"],
                capture_output=True, text=True, timeout=5,
            )
        else:
            result = subprocess.run(
                ["which", "whisper-cli"],
                capture_output=True, text=True, timeout=5,
            )
        if result.returncode == 0:
            path = result.stdout.strip().splitlines()[0]
            if os.path.isfile(path):
                return path
    except Exception:
        pass

    # Check common install locations
    candidates = [
        "whisper-cli",
        "whisper.cpp/build/bin/Release/whisper-cli",
        "whisper.cpp/build/bin/whisper-cli",
        os.path.join(os.path.expanduser("~"), "whisper.cpp", "build", "bin", "Release", "whisper-cli"),
        os.path.join(os.path.expanduser("~"), "whisper.cpp", "build", "bin", "whisper-cli"),
        "/usr/local/bin/whisper-cli",
    ]
    for cand in candidates:
        for ext in ("", ".exe"):
            path = cand + ext
            if os.path.isfile(path):
                return path

    return None


def _find_model(model_name: str = "tiny", model_path: Optional[str] = None) -> Optional[str]:
    """Locate a whisper.cpp GGML model file."""
    if model_path and os.path.isfile(model_path):
        return model_path

    model_file = f"ggml-{model_name}.bin"
    search_dirs = [
        ".",
        "models",
        "whisper.cpp/models",
        os.path.join(os.path.expanduser("~"), "whisper.cpp", "models"),
    ]
    for d in search_dirs:
        path = os.path.join(d, model_file)
        if os.path.isfile(path):
            return path
    return None


def transcribe_whisper_cpp(
    audio_path: str,
    model_name: str = "tiny",
    model_path: Optional[str] = None,
    language: str = "en",
) -> str:
    """Transcribe audio using whisper.cpp CLI.

    Args:
        audio_path: Path to the audio file.
        model_name: Whisper model size (tiny, base, small, medium, large).
        model_path: Explicit path to the GGML model file.
        language: Language code (default: 'en').

    Returns:
        Transcribed text string, or empty string on failure.
    """
    if not os.path.isfile(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return ""

    cli = _find_whisper_cli()
    if not cli:
        logger.warning("whisper-cli not found in PATH — cannot use whisper.cpp.")
        return ""

    model = _find_model(model_name, model_path)
    if not model:
        logger.error("Whisper model not found for '%s'.", model_name)
        return ""

    try:
        result = subprocess.run(
            [
                cli,
                "-f", audio_path,
                "-m", model,
                "-l", language,
                "-ot",       # output text only
                "--no-timestamps",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            logger.info("whisper.cpp transcribed %d chars from %s", len(text), audio_path)
            return text
        else:
            logger.error("whisper.cpp error (rc=%d): %s", result.returncode, result.stderr[:500])
            return ""
    except subprocess.TimeoutExpired:
        logger.error("whisper.cpp timed out on %s", audio_path)
        return ""
    except Exception as e:
        logger.error("whisper.cpp error: %s", e)
        return ""


def transcribe_faster_whisper(
    audio_path: str,
    model_size: str = "tiny",
    device: str = "auto",
    compute_type: str = "default",
) -> str:
    """Transcribe audio using the faster-whisper Python package.

    Args:
        audio_path: Path to the audio file.
        model_size: Model size (tiny, base, small, medium, large-v3).
        device: Device to use ('auto', 'cpu', 'cuda').
        compute_type: Precision (e.g. 'default', 'float16', 'int8_float16').

    Returns:
        Transcribed text string, or empty string on failure.
    """
    if not os.path.isfile(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return ""

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper not installed. Run: pip install faster-whisper")
        return ""

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, _ = model.transcribe(audio_path, language="en")
        text = " ".join(seg.text for seg in segments)
        logger.info("faster-whisper transcribed %d chars from %s", len(text), audio_path)
        return text.strip()
    except Exception as e:
        logger.error("faster-whisper error: %s", e)
        return ""


def transcribe(audio_path: str) -> str:
    """Transcribe audio using whisper.cpp CLI, falling back to faster-whisper.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Transcribed text, or empty string if all methods fail.
    """
    # Try whisper.cpp first
    text = transcribe_whisper_cpp(audio_path)
    if text:
        return text

    # Fall back to faster-whisper
    logger.info("whisper.cpp unavailable — trying faster-whisper fallback.")
    return transcribe_faster_whisper(audio_path)
