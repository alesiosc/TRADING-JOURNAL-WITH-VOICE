"""
Screenshot capture module using MSS with optional region selection via tkinter overlay.

Functions:
    capture_fullscreen() -> str      — capture all monitors, save to screenshots/
    capture_region() -> str          — interactive region selection via tkinter
    capture(region=False) -> str     — auto-mode: fullscreen or region

Uses mss for cross-platform screen capture.
Saves timestamped PNGs to the project's screenshots/ directory.
"""

import logging
import os
import threading
import uuid
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger("screenshot.capture")

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "screenshots")


def _ensure_dir(directory: str) -> str:
    """Ensure directory exists and return its path."""
    os.makedirs(directory, exist_ok=True)
    return directory


def _generate_filename(prefix: str = "screenshot") -> str:
    """Generate a timestamped unique filename."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{uid}.png"


def capture_fullscreen(output_dir: Optional[str] = None) -> Optional[str]:
    """Capture all monitors (combined) and save to a PNG file.

    Args:
        output_dir: Directory to save the screenshot.
                    Defaults to PROJECT_ROOT/screenshots.

    Returns:
        Absolute path to the saved PNG, or None on failure.
    """
    if mss is None:
        logger.error("mss not installed. Run: pip install mss")
        return None

    output_dir = _ensure_dir(output_dir or DEFAULT_SCREENSHOTS_DIR)
    filename = _generate_filename("fullscreen")
    filepath = os.path.join(output_dir, filename)

    try:
        with mss.mss() as sct:
            sct.shot(output=filepath)
        logger.info("Fullscreen screenshot saved: %s", filepath)
        return os.path.abspath(filepath)
    except Exception as e:
        logger.error("Fullscreen capture failed: %s", e)
        return None


def capture_region(output_dir: Optional[str] = None) -> Optional[str]:
    """Open an interactive tkinter overlay to select a screen region.

    The user clicks and drags to select an area, which is captured and saved.

    Args:
        output_dir: Directory to save the screenshot.

    Returns:
        Absolute path to the saved PNG, or None if cancelled/failed.
    """
    if mss is None:
        logger.error("mss not installed. Run: pip install mss")
        return None

    output_dir = _ensure_dir(output_dir or DEFAULT_SCREENSHOTS_DIR)
    filename = _generate_filename("region")
    filepath = os.path.join(output_dir, filename)

    region = _tkinter_region_selector()
    if region is None:
        logger.info("Region selection cancelled.")
        return None

    left, top, width, height = region

    try:
        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        logger.info("Region screenshot saved: %s", filepath)
        return os.path.abspath(filepath)
    except Exception as e:
        logger.error("Region capture failed: %s", e)
        return None


def _tkinter_region_selector() -> Optional[Tuple[int, int, int, int]]:
    """Open a tkinter overlay for region selection.

    Returns:
        (left, top, width, height) tuple, or None if cancelled.
    """
    try:
        import tkinter as tk
    except ImportError:
        logger.error("tkinter not available for region selection.")
        return None

    region = {"start_x": None, "start_y": None, "end_x": None, "end_y": None}
    selection_made = threading.Event()
    result_container = [None]

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.configure(cursor="crosshair")

    canvas = tk.Canvas(root, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    rect_id = None

    def on_mouse_down(event):
        nonlocal rect_id
        region["start_x"] = event.x_root
        region["start_y"] = event.y_root
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=3,
        )

    def on_mouse_move(event):
        nonlocal rect_id
        if region["start_x"] is not None and rect_id:
            canvas.coords(
                rect_id,
                region["start_x"], region["start_y"],
                event.x_root, event.y_root,
            )

    def on_mouse_up(event):
        region["end_x"] = event.x_root
        region["end_y"] = event.y_root
        x1, y1 = region["start_x"], region["start_y"]
        x2, y2 = region["end_x"], region["end_y"]
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        if width > 10 and height > 10:
            result_container[0] = (left, top, width, height)
        root.quit()

    def on_escape(event):
        result_container[0] = None
        root.quit()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass

    return result_container[0]


def capture(region: bool = False, output_dir: Optional[str] = None) -> Optional[str]:
    """Capture a screenshot — fullscreen or interactive region.

    Args:
        region: If True, open the interactive region selector.
        output_dir: Directory to save screenshots.

    Returns:
        Absolute path to saved PNG, or None on failure.
    """
    if region:
        return capture_region(output_dir)
    return capture_fullscreen(output_dir)
