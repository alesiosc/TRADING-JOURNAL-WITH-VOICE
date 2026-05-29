"""Test the vision analysis service."""
import asyncio
import json
import os
import sys
import tempfile

from io import BytesIO
from PIL import Image, ImageDraw

# Ensure the backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vision_analysis import analyze_screenshot


async def main():
    # Create a test chart-like image
    img = Image.new("RGB", (400, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Draw a simple uptrend line
    for x in range(0, 400, 5):
        y = 180 - (x * 0.3)  # uptrend
        draw.rectangle([x, y, x + 3, y + 3], fill=(0, 100, 255))

    # Support/resistance lines
    draw.line([(50, 100), (350, 100)], fill=(255, 0, 0), width=2)
    draw.line([(50, 150), (350, 150)], fill=(0, 200, 0), width=2)
    draw.text((10, 10), "TEST CHART - UPTREND", fill=(0, 0, 0))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f, format="PNG")
        test_path = f.name

    print(f"Test image: {test_path} ({os.path.getsize(test_path)} bytes)")

    try:
        result = await analyze_screenshot(test_path)
        print("\n=== VISION ANALYSIS RESULT ===")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"{type(e).__name__}: {e}")
    finally:
        os.unlink(test_path)


if __name__ == "__main__":
    asyncio.run(main())
