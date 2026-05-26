"""Screen capture logic using MSS (mss library).

Supports:
- Active monitor detection: finds which monitor the foreground window is on
  (Windows-only via win32gui; falls back to primary monitor on other platforms)
- Specific monitor capture: "monitor_1", "monitor_2" etc.
- All-monitors combined capture: "all"
- Saves timestamped PNGs to the configured output directory.
"""

import os
import uuid
import time
import threading
from datetime import datetime
from typing import Optional

import mss
import mss.tools


class ScreenCapturer:
    """Captures screenshots using MSS with user-configurable monitor targeting."""

    # Cache for last active monitor to avoid excessive win32gui calls
    _last_active_monitor = None
    _last_active_check = 0

    def __init__(self, config: dict):
        self.config = config
        self._lock = threading.Lock()

    def capture(self) -> tuple[str, str]:
        """Take a screenshot based on the configured capture_mode.

        Returns:
            (absolute_file_path, relative_url_path) tuple.
            relative_url_path is the path component for serving via /uploads/.
        """
        mode = self.config.get("capture_mode", "active_monitor")
        output_dir = self.config["_output_dir_abs"]

        # Determine which monitor(s) to capture
        monitor_index = self._resolve_monitor_index(mode)  # None if all
        monitors = self._get_monitors_to_capture(monitor_index)

        with mss.mss() as sct:
            # Build filename with timestamp + uuid
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"screenshot_{timestamp}_{unique_id}.png"
            file_path = os.path.join(output_dir, filename)

            if len(monitors) == 1 or (monitor_index is not None and len(monitors) == 1):
                # Single monitor capture
                sct.output = file_path
                try:
                    sct.shot(monitor=monitors[0], output=file_path)
                except Exception:
                    # Fall back to all-in-one
                    sct.shot(output=file_path)
            else:
                # All monitors combined
                self._capture_all_monitors_combined(sct, monitors, file_path)

        # Build the relative URL path (for serving via /uploads/static)
        # output_dir is like .../backend/uploads/screenshots
        # We want /uploads/screenshots/filename
        parts = output_dir.replace("\\", "/").split("/")
        try:
            upload_idx = parts.index("uploads")
            rel_path = "/" + "/".join(parts[upload_idx:]) + "/" + filename
        except ValueError:
            rel_path = "/uploads/screenshots/" + filename

        return file_path, rel_path

    def _resolve_monitor_index(self, mode: str) -> Optional[int]:
        """Convert capture_mode string to MSS monitor index.

        Returns:
            int index (1-based for MSS), or None for 'all' mode.
        """
        if mode == "all":
            return None
        if mode == "active_monitor":
            return self._find_active_monitor_index()
        if mode.startswith("monitor_"):
            try:
                idx = int(mode.split("_")[1])
                return max(1, idx)
            except (ValueError, IndexError):
                return 1
        return 1  # default to primary

    def _get_monitors_to_capture(self, monitor_index: Optional[int]) -> list:
        """Get the list of monitor dicts to capture.

        Args:
            monitor_index: None for all monitors, or int for a specific monitor.

        Returns:
            List of monitor dicts (MSS format: left, top, width, height).
        """
        with mss.mss() as sct:
            all_monitors = sct.monitors  # index 0 = combined, 1..N = individual
            if monitor_index is None:
                # Return the combined monitor (index 0)
                return [all_monitors[0]]
            if 1 <= monitor_index < len(all_monitors):
                return [all_monitors[monitor_index]]
            # Fallback: use the combined monitor
            return [all_monitors[0]]

    def _find_active_monitor_index(self) -> int:
        """Detect which monitor the foreground window is currently on.

        Windows: uses win32gui to get foreground window rect.
        Other platforms: falls back to primary monitor (index 1).

        Returns:
            MSS monitor index (1-based).
        """
        # Cache result for 1 second to avoid hammering win32gui on hotkey spam
        now = time.time()
        if now - self._last_active_check < 1.0 and self._last_active_monitor is not None:
            return self._last_active_monitor

        try:
            import win32gui
            import win32api
        except ImportError:
            # Fallback: primary monitor
            return 1

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                fg_left = rect[0]
                fg_top = rect[1]
                fg_center_x = fg_left + (rect[2] - rect[0]) // 2
                fg_center_y = fg_top + (rect[3] - rect[1]) // 2

                with mss.mss() as sct:
                    monitors = sct.monitors
                    for idx in range(1, len(monitors)):
                        m = monitors[idx]
                        if (m["left"] <= fg_center_x <= m["left"] + m["width"] and
                                m["top"] <= fg_center_y <= m["top"] + m["height"]):
                            self._last_active_monitor = idx
                            self._last_active_check = now
                            return idx

            # Fallback to primary
            self._last_active_monitor = 1
            self._last_active_check = now
            return 1

        except Exception:
            return 1

    def _capture_all_monitors_combined(self, sct, monitors: list, file_path: str):
        """Capture all monitors and create a combined screenshot image.

        Uses PIL/Pillow to stitch screenshots together horizontally/side-by-side.
        Falls back to capturing just the primary monitor if Pillow not available.
        """
        try:
            from PIL import Image as PILImage
        except ImportError:
            # Fallback: capture the first monitor only
            sct.shot(monitor=monitors[0], output=file_path)
            return

        screenshots = []
        total_width = 0
        max_height = 0

        for mon in monitors:
            screenshot = sct.grab(mon)
            img = PILImage.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            screenshots.append(img)
            total_width += img.width
            if img.height > max_height:
                max_height = img.height

        combined = PILImage.new("RGB", (total_width, max_height))
        x_offset = 0
        for img in screenshots:
            combined.paste(img, (x_offset, 0))
            x_offset += img.width

        combined.save(file_path, "PNG")
