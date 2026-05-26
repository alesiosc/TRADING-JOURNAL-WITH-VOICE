"""
Vosk handler — offline speech-to-text using Vosk for low-end hardware.

Function:
    transcribe(audio_path) -> str

Requires:
    pip install vosk
    Download a model from https://alphacephei.com/vosk/models
    (e.g. vosk-model-small-en-us-0.15 for English)
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger("voice.vosk")


def transcribe(
    audio_path: str,
    model_path: str = "vosk-model-small-en-us-0.15",
) -> str:
    """Transcribe audio using Vosk offline ASR.

    Args:
        audio_path: Path to a WAV or other audio file.
        model_path: Path to the Vosk model directory.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    if not os.path.isfile(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return ""

    if not os.path.isdir(model_path):
        logger.error("Vosk model not found at '%s'.", model_path)
        logger.error("Download from https://alphacephei.com/vosk/models (e.g. vosk-model-small-en-us-0.15)")
        return ""

    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        logger.warning("vosk not installed. Run: pip install vosk")
        return ""

    try:
        import wave

        # Try to open as WAV directly
        try:
            wf = wave.open(audio_path, "rb")
            needs_conversion = (
                wf.getnchannels() != 1
                or wf.getsampwidth() != 2
                or wf.getframerate() != 16000
            )
            if needs_conversion:
                wf.close()
                audio_path = _convert_to_mono_16k(audio_path)
                wf = wave.open(audio_path, "rb")
        except wave.Error:
            # Not a WAV file — convert
            audio_path = _convert_to_mono_16k(audio_path)
            wf = wave.open(audio_path, "rb")

        model = Model(model_path)
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        result = json.loads(rec.FinalResult())
        text = result.get("text", "")
        wf.close()
        logger.info("Vosk transcribed: %s", text[:120])
        return text

    except Exception as e:
        logger.error("Vosk error: %s", e)
        return ""


def _convert_to_mono_16k(input_path: str) -> str:
    """Convert audio to mono 16kHz WAV using ffmpeg.

    Returns:
        Path to the converted temporary file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                "-sample_fmt", "s16",
                tmp_path,
            ],
            capture_output=True,
            timeout=60,
        )
        return tmp_path
    except Exception as e:
        logger.warning("ffmpeg conversion failed: %s", e)
        # Return original path as last resort
        return input_path
