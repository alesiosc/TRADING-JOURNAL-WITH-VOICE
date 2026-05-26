"""
Capture controller — ties the hotkey listener and screen capture engine together.

Manages the lifecycle of the screenshot module:
  - Loads configuration
  - Starts/stops the hotkey listener
  - Calls the screen capture engine
  - Optionally records the capture in the database and broadcasts via WebSocket
"""

import os
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

import yaml

from .screen_capture import capture_screenshot
from .hotkey_listener import ScreenshotHotkeyListener


class CaptureController:
    """
    Orchestrates the screenshot module components.

    Usage (standalone):
        ctrl = CaptureController()
        ctrl.start()           # starts hotkey listener
        ctrl.capture_now()     # manual trigger
        ctrl.stop()            # cleanup

    Usage (from FastAPI):
        ctrl = CaptureController()
        result = ctrl.capture_now()
        # result contains file_path, url_path, png_bytes, etc.
    """

    def __init__(
        self,
        config_path: str = None,
        on_capture_callback: Optional[Callable[[dict], None]] = None,
    ):
        """
        Args:
            config_path: Path to config.yaml. If None, uses the default
                         alongside this file.
            on_capture_callback: Optional callback invoked after each capture
                                 with the result dict. Useful for WebSocket
                                 broadcast or DB recording.
        """
        self.config = self._load_config(config_path)
        self.on_capture_callback = on_capture_callback
        self.hotkey_listener: Optional[ScreenshotHotkeyListener] = None
        self._lock = threading.Lock()
        self._active_trade_id: Optional[int] = None

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    @staticmethod
    def _load_config(config_path: Optional[str] = None) -> dict:
        """Load and return the YAML configuration."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

        if not os.path.exists(config_path):
            print(f"⚠️  Config not found at {config_path}, using defaults")
            return {
                "hotkey": "scroll_lock",
                "capture_mode": "active_monitor",
                "save_dir": "backend/uploads/screenshots",
                "auto_capture_on_events": True,
                "timestamp_format": "%Y%m%d_%H%M%S",
            }

        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def get_save_dir(self) -> str:
        """Resolve the save directory path (absolute)."""
        save_dir = self.config.get("save_dir", "backend/uploads/screenshots")
        if not os.path.isabs(save_dir):
            # Resolve relative to project root (parent of screenshot_module/)
            save_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", save_dir)
            )
        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    # ------------------------------------------------------------------
    # Active trade tracking
    # ------------------------------------------------------------------
    @property
    def active_trade_id(self):
        return self._active_trade_id

    @active_trade_id.setter
    def active_trade_id(self, trade_id: Optional[int]):
        self._active_trade_id = trade_id

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------
    def capture_now(self, filename_prefix: str = "screenshot") -> dict:
        """
        Trigger an immediate screenshot capture.

        Args:
            filename_prefix: Prefix for the saved file.

        Returns:
            dict with keys: file_path, url_path, width, height, monitor, png_bytes
        """
        with self._lock:
            save_dir = self.get_save_dir()
            capture_mode = self.config.get("capture_mode", "active_monitor")
            monitor_index = self.config.get("monitor_index", 1)
            timestamp_fmt = self.config.get("timestamp_format", "%Y%m%d_%H%M%S")

            result = capture_screenshot(
                save_dir=save_dir,
                filename_prefix=filename_prefix,
                capture_mode=capture_mode,
                monitor_index=monitor_index,
                timestamp_format=timestamp_fmt,
            )

            if self.on_capture_callback:
                try:
                    self.on_capture_callback(result)
                except Exception as e:
                    print(f"⚠️  Capture callback error: {e}")

            print(f"📸 Screenshot saved: {result['file_path']}")
            return result

    # ------------------------------------------------------------------
    # Hotkey listener
    # ------------------------------------------------------------------
    def start_hotkey_listener(self):
        """Start the global hotkey listener."""
        if self.hotkey_listener is not None:
            print("⚠️  Hotkey listener already started")
            return

        hotkey = self.config.get("hotkey", "scroll_lock")
        self.hotkey_listener = ScreenshotHotkeyListener(
            hotkey=hotkey,
            callback=self.capture_now,
        )
        self.hotkey_listener.start()

    def stop_hotkey_listener(self):
        """Stop the global hotkey listener."""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        """Start the screenshot module (hotkey listener only)."""
        self.start_hotkey_listener()
        print("✅ Screenshot Module started")

    def stop(self):
        """Stop and clean up the screenshot module."""
        self.stop_hotkey_listener()
        print("✅ Screenshot Module stopped")

    def cleanup(self):
        """Alias for stop()."""
        self.stop()
