"""
Screen capture engine using MSS.

Captures the active monitor (the one containing the foreground window on Windows)
or a full-screen/all-monitors capture based on configuration.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import mss
    import mss.tools
except ImportError:
    mss = None
    mss_tools = None


def _get_monitor_with_foreground_window(mss_instance):
    """
    Detect which monitor contains the foreground (active) window on Windows.

    Uses ctypes to call GetForegroundWindow and GetWindowRect, then
    determines which monitor's bounds contain that window's center point.

    Falls back to monitor 1 (primary) if detection fails or on non-Windows.
    """
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return mss_instance.monitors[1]  # fallback to primary

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        win_left = rect.left
        win_top = rect.top
        win_right = rect.right
        win_bottom = rect.bottom

        # Window center
        cx = (win_left + win_right) // 2
        cy = (win_top + win_bottom) // 2

        # Find which monitor contains the center point
        for monitor in mss_instance.monitors[1:]:  # skip monitor 0 (virtual)
            m_left = monitor["left"]
            m_top = monitor["top"]
            m_right = monitor["left"] + monitor["width"]
            m_bottom = monitor["top"] + monitor["height"]
            if m_left <= cx <= m_right and m_top <= cy <= m_bottom:
                return monitor

        # Fallback: monitor closest to window center
        best = None
        best_dist = float("inf")
        for monitor in mss_instance.monitors[1:]:
            mc_x = monitor["left"] + monitor["width"] // 2
            mc_y = monitor["top"] + monitor["height"] // 2
            dist = (mc_x - cx) ** 2 + (mc_y - cy) ** 2
            if dist < best_dist:
                best_dist = dist
                best = monitor
        return best or mss_instance.monitors[1]

    except Exception:
        # Non-Windows or detection failure — use primary monitor
        if mss_instance:
            return mss_instance.monitors[1]
        return None


def capture_active_monitor():
    """
    Capture the monitor that currently has the foreground (active) window.

    Returns:
        tuple: (bytes, monitor_info) — raw PNG bytes and the monitor dict.
    """
    if mss is None:
        raise ImportError("mss is not installed. Run: pip install mss")

    with mss.mss() as sct:
        monitor = _get_monitor_with_foreground_window(sct)
        screenshot = sct.grab(monitor)
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        return png_bytes, monitor


def capture_full_screen():
    """
    Capture all monitors merged into one wide screenshot (monitor 0 in MSS).

    Returns:
        tuple: (bytes, monitor_info) — raw PNG bytes and the virtual monitor dict.
    """
    if mss is None:
        raise ImportError("mss is not installed. Run: pip install mss")

    with mss.mss() as sct:
        monitor = sct.monitors[0]  # virtual full screen across all monitors
        screenshot = sct.grab(monitor)
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        return png_bytes, monitor


def capture_single_monitor(monitor_index: int = 1):
    """
    Capture a specific monitor by index (1-based in MSS: 1 = primary).

    Args:
        monitor_index: 1-based monitor index (1 = primary, 2, 3, ...)

    Returns:
        tuple: (bytes, monitor_info) — raw PNG bytes and the monitor dict.
    """
    if mss is None:
        raise ImportError("mss is not installed. Run: pip install mss")

    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index < 0 or monitor_index >= len(monitors):
            raise ValueError(
                f"Monitor index {monitor_index} out of range. "
                f"Available monitors: 0 (virtual) through {len(monitors) - 1}"
            )
        monitor = monitors[monitor_index]
        screenshot = sct.grab(monitor)
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        return png_bytes, monitor


def capture_screenshot(
    save_dir: str = None,
    filename_prefix: str = "screenshot",
    capture_mode: str = "active_monitor",
    monitor_index: int = 1,
    timestamp_format: str = "%Y%m%d_%H%M%S",
) -> dict:
    """
    High-level capture function: captures and optionally saves a screenshot.

    Args:
        save_dir: Directory to save the PNG file. If None, returns bytes only.
        filename_prefix: Prefix for the saved filename.
        capture_mode: "active_monitor", "full_screen", or "single_monitor".
        monitor_index: Used when capture_mode = "single_monitor".
        timestamp_format: strftime format for the filename.

    Returns:
        dict with keys:
            - "file_path": absolute path to saved file (or None if save_dir is None)
            - "url_path": relative URL path for serving via FastAPI (or None)
            - "width": pixel width of captured monitor
            - "height": pixel height of captured monitor
            - "monitor": the monitor dict from MSS
            - "png_bytes": raw PNG bytes
    """
    if capture_mode == "full_screen":
        png_bytes, monitor = capture_full_screen()
    elif capture_mode == "single_monitor":
        png_bytes, monitor = capture_single_monitor(monitor_index)
    else:  # default: active_monitor
        png_bytes, monitor = capture_active_monitor()

    width = monitor.get("width", 0)
    height = monitor.get("height", 0)

    result = {
        "file_path": None,
        "url_path": None,
        "width": width,
        "height": height,
        "monitor": monitor,
        "png_bytes": png_bytes,
    }

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime(timestamp_format)
        filename = f"{filename_prefix}_{timestamp}.png"
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            f.write(png_bytes)
        result["file_path"] = os.path.abspath(file_path)
        # URL path for FastAPI static serving
        # save_dir expected to be something like backend/uploads/screenshots
        # The static mount is at /uploads/ serving from backend/uploads/
        result["url_path"] = f"/uploads/screenshots/{filename}"

    return result
