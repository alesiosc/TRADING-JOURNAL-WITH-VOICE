"""
Trading Journal — Voice Input Module

Unified VoiceHandler that tries transcription backends in order:
    1. Whisper.cpp CLI (fastest, local)
    2. faster-whisper (Python package fallback)
    3. Vosk (low-end offline fallback)
    4. Browser Speech API (last resort / web-based)

Usage:
    from voice import VoiceHandler

    handler = VoiceHandler()
    text = handler.transcribe("voice_recordings/trade.wav")

    # Parse trade dictation
    trade = handler.parse("long ES 2 contracts at 5032.50")
    print(trade["symbol"])  # "ES"

    # Start hotkey recording
    handler.start_recorder()
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("voice")

# Import submodule transcribe functions
from .whisper_handler import transcribe as transcribe_whisper
from .vosk_handler import transcribe as transcribe_vosk
from .trade_parser import parse as parse_trade
from .hotkey_recorder import HotkeyRecorder, record_audio_blocking


class VoiceHandler:
    """Unified voice input handler with multi-backend transcription.

    Transcribes audio using the best available backend:
        whisper.cpp CLI -> faster-whisper -> Vosk -> Browser API

    Also provides trade dictation parsing and hotkey-activated recording.
    """

    def __init__(
        self,
        recording_dir: str = "voice_recordings",
        whisper_model: str = "tiny",
        vosk_model_path: str = "vosk-model-small-en-us-0.15",
    ):
        self.recording_dir = recording_dir
        self.whisper_model = whisper_model
        self.vosk_model_path = vosk_model_path
        self._recorder: Optional[HotkeyRecorder] = None
        os.makedirs(self.recording_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio using best available backend.

        Order: whisper.cpp CLI -> faster-whisper -> Vosk -> browser_api.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Transcribed text, or empty string if all methods fail.
        """
        # 1. Try whisper.cpp CLI
        text = transcribe_whisper(audio_path)
        if text:
            return text

        # 2. Vosk fallback
        logger.info("whisper backends unavailable — trying Vosk.")
        text = transcribe_vosk(audio_path, model_path=self.vosk_model_path)
        if text:
            return text

        # 3. Browser Speech API fallback (last resort)
        logger.info("Vosk unavailable — trying Browser Speech API fallback.")
        text = self._transcribe_browser_api(audio_path)
        return text

    def _transcribe_browser_api(self, audio_path: str) -> str:
        """Fallback: use the Web Speech API via a headless browser.

        This is a minimal implementation that attempts to use the
        browser's built-in speech recognition as a last resort.
        """
        try:
            import subprocess
            import json
            import tempfile

            # Create an HTML page that uses the Web Speech API
            html = """<!DOCTYPE html>
<html><body>
<script>
const fileInput = document.createElement('input');
fileInput.type = 'file';
fileInput.accept = 'audio/*';
fileInput.onchange = async function(e) {
    const file = e.target.files[0];
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = function(event) {
        document.body.textContent = event.results[0][0].transcript;
    };
    recognition.onerror = function() {
        document.body.textContent = '__ERROR__';
    };
    recognition.start();
};
fileInput.click();
</script></body></html>"""
            tmp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w")
            tmp_html.write(html)
            tmp_html.close()

            logger.warning("Browser Speech API fallback requires manual intervention.")
            logger.warning("Open %s in a browser and select the audio file.", tmp_html.name)
            return ""
        except Exception as e:
            logger.error("Browser API fallback error: %s", e)
            return ""

    # ------------------------------------------------------------------
    # Trade dictation parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse(text: str) -> Optional[dict]:
        """Parse a natural language trade dictation into a structured dict.

        Args:
            text: Natural language description (e.g. "long ES 2 at 5032").

        Returns:
            dict with keys: direction, symbol, quantity, entry_price,
            stop_loss, take_profit, raw_text.
        """
        return parse_trade(text)

    # ------------------------------------------------------------------
    # Audio recording
    # ------------------------------------------------------------------

    def record_audio(self, duration: float = 10.0) -> Optional[str]:
        """Record audio from the microphone immediately.

        Args:
            duration: Recording duration in seconds.

        Returns:
            Path to the recorded WAV file, or None on failure.
        """
        return record_audio_blocking(
            output_path=os.path.join(self.recording_dir, "voice_manual.wav"),
            duration=duration,
        )

    def start_recorder(
        self,
        hotkey: str = "ctrl+shift+v",
        duration: float = 10.0,
        on_complete=None,
    ) -> None:
        """Start the global hotkey recorder in the background.

        Args:
            hotkey: Keyboard combination to trigger recording.
            duration: Recording duration in seconds.
            on_complete: Optional callback(filepath) when recording finishes.
        """
        if self._recorder:
            logger.info("Recorder already running.")
            return

        self._recorder = HotkeyRecorder(
            hotkey=hotkey,
            output_dir=self.recording_dir,
            duration=duration,
            on_complete=on_complete,
        )
        self._recorder.start()

    def stop_recorder(self) -> None:
        """Stop the hotkey recorder."""
        if self._recorder:
            self._recorder.stop()
            self._recorder = None


# ------------------------------------------------------------------
# Convenience functions (backward-compatible with existing code)
# ------------------------------------------------------------------

def transcribe_voice(audio_path: str) -> str:
    """Convenience: transcribe an audio file using default settings."""
    handler = VoiceHandler()
    return handler.transcribe(audio_path)


def parse_trade_text(text: str) -> Optional[dict]:
    """Convenience: parse trade dictation text."""
    return parse_trade(text)
