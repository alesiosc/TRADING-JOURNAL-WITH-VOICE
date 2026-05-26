"""
Screenshot Capture Module — configurable screenshot utility with global hotkey,
active/specific-monitor capture, OCR, annotation, and API integration.

Sub-modules:
    capture         — Fullscreen and region capture via MSS (tkinter overlay)
    ocr             — Text extraction via PaddleOCR / pytesseract
    hotkey_capture  — Global hotkey listener for capture+save+OCR
    annotator       — Draw entry/exit markers on screenshots
    capturer        — ScreenCapturer (MSS with monitor targeting)
    controller      — ScreenshotController (capture orchestration)
    hotkey_listener — HotkeyListener (pynput-based)

Usage:
    from screenshot_module import ScreenshotModule

    mod = ScreenshotModule()
    mod.start()          # start hotkey listener
    mod.capture()        # take a screenshot right now (returns file path)
    mod.stop()           # stop hotkey listener

    # New modules:
    from screenshot_module.capture import capture, capture_region, capture_fullscreen
    from screenshot_module.ocr import extract_text
    from screenshot_module.hotkey_capture import HotkeyCapture
    from screenshot_module.annotator import annotate
"""

import yaml
import os
import threading

from .controller import ScreenshotController
from .capturer import ScreenCapturer
from .hotkey_listener import HotkeyListener

# Expose new modules at package level for convenience
from . import capture
from . import ocr
from . import hotkey_capture
from . import annotator


class ScreenshotModule:
    """Main interface for the screenshot module.

    Loads user configuration from config.yaml, wires together the capturer,
    hotkey listener, and controller. Provides start/stop/capture methods.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self._capturer = None
        self._listener = None
        self._controller = None
        self._running = False

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    def start(self) -> None:
        """Start the screenshot module — initializes capturer and hotkey listener."""
        if not self.enabled:
            print("⏹️  Screenshot module is disabled in config.yaml")
            return

        if self._running:
            print("ℹ️  Screenshot module already running")
            return

        # Resolve output directory
        output_dir = self.config.get("output_dir", "backend/uploads/screenshots")
        if not os.path.isabs(output_dir):
            # Relative to project root (parent of screenshot_module/)
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir)
        os.makedirs(output_dir, exist_ok=True)
        self.config["_output_dir_abs"] = output_dir

        # Create components
        self._capturer = ScreenCapturer(self.config)
        self._controller = ScreenshotController(self._capturer, self.config)

        # Start hotkey listener if enabled
        hk_config = self.config.get("hotkey", {})
        if hk_config.get("enabled", True):
            key = hk_config.get("key", "<ctrl>+<shift>+s")
            self._listener = HotkeyListener(key, self._controller.handle_hotkey)
            self._listener.start()

        self._running = True
        print("📸 Screenshot module started" +
              (f" — hotkey: {hk_config.get('key', '<ctrl>+<shift>+s')}" if hk_config.get("enabled", True) else ""))

    def capture(self, trade_id: int = None, event: str = None) -> str:
        """Take a screenshot immediately and save it.

        Args:
            trade_id: Optional trade ID to associate the screenshot with.
            event: Optional trigger event name (entry, exit, sl_move, etc.).

        Returns:
            Absolute path to the saved PNG file, or None if disabled.
        """
        if not self.enabled:
            return None
        if self._controller is None:
            self.start()
        return self._controller.capture(trade_id=trade_id, event=event)

    def stop(self) -> None:
        """Stop the module — stops hotkey listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
        print("⏹️  Screenshot module stopped")

    @property
    def is_running(self) -> bool:
        return self._running


def create_screenshot_module(config_path: str = None) -> ScreenshotModule:
    """Convenience factory function."""
    return ScreenshotModule(config_path)
