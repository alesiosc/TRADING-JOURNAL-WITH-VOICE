"""
Screenshot annotator — draws entry/exit markers on trading screenshots.

Functions:
    annotate(image_path, trades) -> str
        Draw entry/exit markers and return path to annotated image.

Supports:
    - Green upward arrow for entry (long) or red downward arrow (short)
    - Red "X" for exit
    - Trade labels with price and quantity
    - Stop loss and take profit level lines
    - Multiple trades on the same screenshot

Dependencies:
    pip install pillow
"""

import logging
import os
from typing import List, Optional, Union

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("screenshot.annotator")

# Colors (RGBA)
COLOR_ENTRY_LONG = (0, 200, 0, 255)      # green
COLOR_ENTRY_SHORT = (220, 40, 40, 255)   # red
COLOR_EXIT = (255, 50, 50, 255)          # bright red
COLOR_STOP_LOSS = (255, 100, 100, 255)   # light red
COLOR_TAKE_PROFIT = (100, 200, 100, 255) # light green
COLOR_LABEL_BG = (30, 30, 30, 200)       # dark semi-transparent
COLOR_LABEL_TEXT = (255, 255, 255, 255)  # white
COLOR_LINE = (255, 255, 0, 180)          # yellow dashed lines for SL/TP

MARKER_SIZE = 16
FONT_SIZE = 14


def _get_font(size: int = FONT_SIZE):
    """Try to load a TrueType font, falling back to default."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except (IOError, OSError):
            return ImageFont.load_default()


def _draw_arrow(draw, x, y, direction: str, size: int = MARKER_SIZE):
    """Draw an entry arrow marker.

    Args:
        draw: ImageDraw instance.
        x, y: Center coordinates of the marker.
        direction: 'long' (up) or 'short' (down).
        size: Arrow size in pixels.
    """
    color = COLOR_ENTRY_LONG if direction == "long" else COLOR_ENTRY_SHORT
    half = size // 2

    if direction == "long":
        # Upward triangle
        points = [
            (x, y - half),
            (x - half, y + half),
            (x + half, y + half),
        ]
    else:
        # Downward triangle
        points = [
            (x, y + half),
            (x - half, y - half),
            (x + half, y - half),
        ]

    draw.polygon(points, fill=color, outline=(255, 255, 255))


def _draw_cross(draw, x, y, size: int = MARKER_SIZE):
    """Draw an X marker (exit)."""
    half = size // 2
    draw.line([(x - half, y - half), (x + half, y + half)],
              fill=COLOR_EXIT, width=3)
    draw.line([(x + half, y - half), (x - half, y + half)],
              fill=COLOR_EXIT, width=3)


def _draw_label(draw, x, y, text: str, anchor: str = "sw"):
    """Draw a semi-transparent label box with text."""
    font = _get_font()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad = 4
    if anchor == "sw":
        lx, ly = x - tw // 2 - pad, y + pad
    elif anchor == "nw":
        lx, ly = x - tw // 2 - pad, y - th - pad * 2
    else:
        lx, ly = x + pad, y - th - pad

    draw.rectangle(
        [lx, ly, lx + tw + pad * 2, ly + th + pad * 2],
        fill=COLOR_LABEL_BG,
    )
    draw.text((lx + pad, ly + pad), text, fill=COLOR_LABEL_TEXT, font=font)


def _draw_level_line(draw, img_width: int, y: int, color, label: str = ""):
    """Draw a horizontal level line (stop loss / take profit)."""
    font = _get_font(12)
    # Dashed line
    dash_len = 10
    x = 0
    while x < img_width:
        x2 = min(x + dash_len, img_width)
        draw.line([(x, y), (x2, y)], fill=color, width=2)
        x += dash_len * 2

    if label:
        draw.text((5, y - 18), label, fill=color, font=font)


def annotate(
    image_path: str,
    trades: Union[dict, List[dict]],
    output_path: Optional[str] = None,
) -> Optional[str]:
    """Draw entry/exit markers on a screenshot.

    Args:
        image_path: Path to the original screenshot.
        trades: A single trade dict or list of trade dicts with fields:
            - direction: 'long' or 'short'
            - entry_price: float (optional, for label)
            - stop_loss: float (optional, draws level line)
            - take_profit: float (optional, draws level line)
            - quantity: float (optional, for label)
            - symbol: str (optional, for label)
            - entry_x, entry_y: pixel coordinates (optional)
              If not provided, markers are placed at image center.
            - exit_x, exit_y: pixel coordinates for exit markers.
        output_path: Where to save the annotated image.
                     Defaults to input filename with '_annotated' suffix.

    Returns:
        Path to the annotated image, or None on failure.
    """
    if not os.path.isfile(image_path):
        logger.error("Image not found: %s", image_path)
        return None

    if isinstance(trades, dict):
        trades = [trades]

    try:
        img = Image.open(image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size
    except Exception as e:
        logger.error("Failed to open image: %s", e)
        return None

    for trade in trades:
        direction = trade.get("direction", "long")
        entry_price = trade.get("entry_price", 0)
        stop_loss = trade.get("stop_loss")
        take_profit = trade.get("take_profit")
        quantity = trade.get("quantity", 0)
        symbol = trade.get("symbol", "")

        # Default position: center of image, slightly offset per trade
        entry_x = trade.get("entry_x", img_width // 2)
        entry_y = trade.get("entry_y", img_height // 2)
        exit_x = trade.get("exit_x")
        exit_y = trade.get("exit_y")

        # Draw entry marker
        if entry_x and entry_y:
            _draw_arrow(draw, int(entry_x), int(entry_y), direction)

            label_parts = []
            if symbol:
                label_parts.append(symbol)
            if quantity:
                label_parts.append(f"{quantity}")
            dir_label = "LONG" if direction == "long" else "SHORT"
            label_parts.append(dir_label)
            if entry_price:
                label_parts.append(f"@{entry_price}")

            _draw_label(draw, int(entry_x), int(entry_y),
                        " ".join(label_parts), anchor="sw")

        # Draw exit marker
        if exit_x and exit_y:
            _draw_cross(draw, int(exit_x), int(exit_y))
            _draw_label(draw, int(exit_x), int(exit_y), "EXIT", anchor="nw")

        # Draw stop loss level line
        if stop_loss is not None and entry_price:
            # Estimate Y position based on price scaling (rough heuristic)
            price_range = abs((take_profit or entry_price * 1.02) - (stop_loss or entry_price * 0.98))
            if price_range > 0:
                # Normalize: put SL below entry for long, above for short
                if direction == "long":
                    ratio = (stop_loss - entry_price) / price_range
                else:
                    ratio = (entry_price - stop_loss) / price_range
                sl_y = entry_y + int(ratio * img_height * 0.3)
                sl_y = max(20, min(img_height - 20, sl_y))
                _draw_level_line(draw, img_width, sl_y, COLOR_STOP_LOSS,
                                 f"SL {stop_loss}")

        # Draw take profit level line
        if take_profit is not None and entry_price:
            price_range = abs((take_profit or entry_price * 1.02) - (stop_loss or entry_price * 0.98))
            if price_range > 0:
                if direction == "long":
                    ratio = (take_profit - entry_price) / price_range
                else:
                    ratio = (entry_price - take_profit) / price_range
                tp_y = entry_y - int(ratio * img_height * 0.3)
                tp_y = max(20, min(img_height - 20, tp_y))
                _draw_level_line(draw, img_width, tp_y, COLOR_TAKE_PROFIT,
                                 f"TP {take_profit}")

    # Save
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_annotated{ext}"

    try:
        img.save(output_path, "PNG")
        logger.info("Annotated screenshot saved: %s", output_path)
        return os.path.abspath(output_path)
    except Exception as e:
        logger.error("Failed to save annotated image: %s", e)
        return None
