"""
Cross-platform hotkey audio recorder.

Uses the `keyboard` library to listen for a global hotkey combination.
When triggered, records audio from the microphone to a timestamped WAV file
in the configured recordings directory.

Usage:
    from voice.hotkey_recorder import HotkeyRecorder

    recorder = HotkeyRecorder(hotkey="ctrl+shift+v", output_dir="voice_recordings")
    recorder.start()
    # ... press Ctrl+Shift+V to record ...
    recorder.stop()

Dependencies:
    - pip install keyboard pyaudio
    - On Linux: sudo apt install python3-pyaudio portaudio19-dev
    - On Windows: pip install pyaudio (or pipwin install pyaudio)
"""

import logging
import os
import tempfile
import threading
import wave
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger("voice.hotkey_recorder")


class HotkeyRecorder:
    """Listens for a global hotkey and records audio on trigger.

    Attributes:
        hotkey: Keyboard combination string (e.g. 'ctrl+shift+v').
        output_dir: Directory where recordings are saved.
        duration: Recording duration in seconds (default: 10).
        on_complete: Optional callback invoked with the recorded file path.
    """

    def __init__(
        self,
        hotkey: str = "ctrl+shift+v",
        output_dir: str = "voice_recordings",
        duration: float = 10.0,
        on_complete: Optional[Callable[[str], None]] = None,
    ):
        self.hotkey = hotkey
        self.output_dir = output_dir
        self.duration = duration
        self.on_complete = on_complete
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._recording = False
        self._lock = threading.Lock()

        os.makedirs(self.output_dir, exist_ok=True)

    def start(self) -> None:
        """Start listening for the hotkey in a background thread."""
        if self._running:
            logger.info("HotkeyRecorder already running.")
            return

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="hotkey-recorder",
        )
        self._listener_thread.start()
        logger.info("HotkeyRecorder started — press '%s' to record (%.1f sec).",
                     self.hotkey, self.duration)

    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        self._listener_thread = None
        logger.info("HotkeyRecorder stopped.")

    def _listen_loop(self) -> None:
        """Background loop: listen for the hotkey and record on press."""
        try:
            import keyboard
        except ImportError:
            logger.error(
                "keyboard library not installed. Run: pip install keyboard\n"
                "On Linux you may need: sudo pip install keyboard"
            )
            return

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey, suppress=True)
            keyboard.wait()  # blocks until keyboard.unhook_all() is called
        except Exception as e:
            logger.error("Hotkey listener error: %s", e)

    def _on_hotkey(self) -> None:
        """Callback when hotkey is pressed — starts recording."""
        with self._lock:
            if self._recording:
                logger.warning("Already recording — ignoring hotkey.")
                return
            self._recording = True

        threading.Thread(target=self._record_audio, daemon=True).start()

    def _record_audio(self) -> None:
        """Record audio from the microphone and save to file."""
        filepath = self._generate_filepath()

        try:
            import pyaudio

            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
            )

            logger.info("Recording for %.1f seconds...", self.duration)
            frames = []
            num_frames = int(16000 / 1024 * self.duration)
            for _ in range(num_frames):
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)
                except Exception:
                    break

            stream.stop_stream()
            stream.close()
            p.terminate()

            wf = wave.open(filepath, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b"".join(frames))
            wf.close()

            logger.info("Saved recording: %s", filepath)

            if self.on_complete:
                try:
                    self.on_complete(filepath)
                except Exception as e:
                    logger.error("on_complete callback error: %s", e)

        except ImportError:
            logger.error("pyaudio not installed. Run: pip install pyaudio")
        except Exception as e:
            logger.error("Recording failed: %s", e)
        finally:
            with self._lock:
                self._recording = False

    def _generate_filepath(self) -> str:
        """Generate a timestamped file path for the recording."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{ts}.wav"
        return os.path.join(self.output_dir, filename)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def record_audio_blocking(
    output_path: Optional[str] = None,
    duration: float = 10.0,
) -> Optional[str]:
    """Record audio immediately and return the file path.

    Args:
        output_path: Where to save the file. Auto-generates if None.
        duration: Recording duration in seconds.

    Returns:
        Path to the recorded WAV file, or None on failure.
    """
    if output_path is None:
        output_dir = "temp_recordings"
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"recording_{ts}.wav")

    try:
        import pyaudio

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )
        logger.info("Recording for %.1f seconds...", duration)
        frames = []
        for _ in range(int(16000 / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(output_path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b"".join(frames))
        wf.close()

        logger.info("Saved recording: %s", output_path)
        return output_path
    except Exception as e:
        logger.error("Recording failed: %s", e)
        return None
