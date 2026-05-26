"""
Global hotkey capture listener.

Listens for a configurable hotkey (default: Ctrl+Shift+S) using the `keyboard`
library. When triggered:
    1. Captures a screenshot via screenshot_module.capture
    2. Saves to the screenshots/ directory
    3. Optionally runs OCR to extract text

Usage:
    from screenshot_module.hotkey_capture import HotkeyCapture

    listener = HotkeyCapture()
    listener.start()
    # ... press Ctrl+Shift+S to capture ...
    listener.stop()

    # Or use the context manager:
    with HotkeyCapture() as listener:
        # hotkey is active
        pass

Dependencies:
    pip install keyboard mss
    (optional) pip install paddleocr  or  pip install pytesseract
"""

import logging
import os
import threading
from datetime import datetime
from typing import Callable, Optional

from .capture import capture as capture_screenshot
from .ocr import extract_text as ocr_extract_text

logger = logging.getLogger("screenshot.hotkey_capture")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")


class HotkeyCapture:
    """Global hotkey listener that captures screenshots and optionally runs OCR.

    Attributes:
        hotkey: The key combination to listen for (default: 'ctrl+shift+s').
        output_dir: Directory to save screenshots.
        on_capture: Optional callback invoked after capture with file path.
        enable_ocr: If True, run OCR on the captured screenshot.
        _listener_thread: Background thread running the listener.
    """

    def __init__(
        self,
        hotkey: str = "ctrl+shift+s",
        output_dir: Optional[str] = None,
        on_capture: Optional[Callable[[str], None]] = None,
        enable_ocr: bool = False,
        ocr_backend: str = "auto",
    ):
        self.hotkey = hotkey
        self.output_dir = output_dir or DEFAULT_SCREENSHOTS_DIR
        self.on_capture = on_capture
        self.enable_ocr = enable_ocr
        self.ocr_backend = ocr_backend
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
        self._last_capture_path: Optional[str] = None

        os.makedirs(self.output_dir, exist_ok=True)

    def start(self) -> None:
        """Start listening for the hotkey in a background thread."""
        if self._running:
            logger.info("HotkeyCapture already running.")
            return

        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="screenshot-hotkey-capture",
        )
        self._listener_thread.start()
        logger.info(
            "HotkeyCapture started — press '%s' to capture (OCR: %s).",
            self.hotkey,
            "on" if self.enable_ocr else "off",
        )

    def stop(self) -> None:
        """Stop the hotkey listener."""
        self._running = False
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        self._listener_thread = None
        logger.info("HotkeyCapture stopped.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    @property
    def last_capture_path(self) -> Optional[str]:
        """Get the path of the most recent capture."""
        return self._last_capture_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _listen_loop(self) -> None:
        """Background loop: listen for hotkey and capture on press."""
        try:
            import keyboard
        except ImportError:
            logger.error(
                "keyboard library not installed. Run: pip install keyboard\n"
                "On Linux: sudo pip install keyboard"
            )
            return

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey, suppress=True)
            keyboard.wait()
        except Exception as e:
            logger.error("Hotkey listener error: %s", e)

    def _on_hotkey(self) -> None:
        """Callback when hotkey is pressed — capture screenshot."""
        logger.info("Hotkey triggered — capturing screenshot...")

        # Capture
        filepath = capture_screenshot(region=False, output_dir=self.output_dir)
        if not filepath:
            logger.error("Screenshot capture failed.")
            return

        self._last_capture_path = filepath
        logger.info("Screenshot captured: %s", filepath)

        # Optional OCR
        if self.enable_ocr:
            threading.Thread(
                target=self._run_ocr,
                args=(filepath,),
                daemon=True,
            ).start()

        # Callback
        if self.on_capture:
            try:
                self.on_capture(filepath)
            except Exception as e:
                logger.error("on_capture callback error: %s", e)

    def _run_ocr(self, filepath: str) -> None:
        """Run OCR on a captured screenshot."""
        logger.info("Running OCR on %s ...", filepath)
        text = ocr_extract_text(filepath, backend=self.ocr_backend)
        if text:
            ocr_log_path = filepath.replace(".png", "_ocr.txt")
            try:
                with open(ocr_log_path, "w") as f:
                    f.write(text)
                logger.info("OCR text saved to %s (%d chars)", ocr_log_path, len(text))
            except Exception as e:
                logger.warning("Could not save OCR text: %s", e)
        else:
            logger.info("No text extracted via OCR.")
