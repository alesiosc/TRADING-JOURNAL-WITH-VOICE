"""ScreenshotController — ties capture, save, and broadcast together.

Orchestrates the screenshot pipeline:
1. Capture screen (via ScreenCapturer)
2. Save to disk
3. Return file path + URL path to caller

Used by:
- HotkeyListener (user presses hotkey → manual capture)
- FastAPI endpoints (POST /api/screenshots/capture and auto-capture)
"""

import os
import threading
from datetime import datetime, timezone
from typing import Optional


class ScreenshotController:
    """Coordinates screen capture, file save, and metadata generation."""

    def __init__(self, capturer, config: dict):
        """
        Args:
            capturer: ScreenCapturer instance.
            config: Module configuration dict (from config.yaml).
        """
        self.capturer = capturer
        self.config = config
        self._lock = threading.Lock()
        self._last_capture_path = None

    def capture(self, trade_id: int = None, event: str = None) -> Optional[str]:
        """Execute a full capture cycle.

        Args:
            trade_id: Optional trade ID to associate the screenshot with.
            event: Optional trigger event name (entry, exit, sl_move, add, modification).

        Returns:
            Absolute file path to the saved PNG, or None if capture failed.
        """
        with self._lock:
            try:
                abs_path, rel_url = self.capturer.capture()
                self._last_capture_path = abs_path

                filename = os.path.basename(abs_path)

                output = {
                    "file_path": abs_path,
                    "url_path": rel_url,
                    "filename": filename,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                }

                if trade_id is not None:
                    output["trade_id"] = trade_id
                if event is not None:
                    output["trigger_event"] = event

                # Auto-capture setting
                output["auto_captured"] = (
                    event is not None
                    and self.config.get("auto_capture_on_events", True)
                )

                # Print to console for visibility
                event_tag = f" [{event}]" if event else ""
                trade_tag = f" (trade #{trade_id})" if trade_id else ""
                print(f"📸 Screenshot captured{event_tag}{trade_tag}: {filename}")

                return output

            except Exception as e:
                print(f"❌ Screenshot capture failed: {e}")
                import traceback
                traceback.print_exc()
                return None

    def handle_hotkey(self):
        """Callback for hotkey press — captures without trade association."""
        self.capture(trade_id=None, event=None)

    @property
    def last_capture_path(self) -> Optional[str]:
        """Get the most recently captured screenshot path."""
        return self._last_capture_path
