"""
Text extraction from screenshots using OCR.

Functions:
    extract_text(image_path) -> str

Primary backend: PaddleOCR (pip install paddleocr)
Fallback:       pytesseract (pip install pytesseract + Tesseract-OCR system install)

PaddleOCR is preferred because it runs fully locally, is free, works well
on charts/numbers, and doesn't require a separate system installation.
"""

import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger("screenshot.ocr")


def extract_text_paddle(image_path: str) -> str:
    """Extract text using PaddleOCR.

    Args:
        image_path: Path to the screenshot image.

    Returns:
        Extracted text string, or empty string on failure.
    """
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        logger.info("PaddleOCR not installed (pip install paddleocr).")
        return ""

    if not os.path.isfile(image_path):
        logger.error("Image not found: %s", image_path)
        return ""

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        result = ocr.ocr(image_path, cls=True)
        if not result or not result[0]:
            return ""

        lines = []
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            if confidence > 0.3:
                lines.append(text)

        text = "\n".join(lines)
        logger.info("PaddleOCR extracted %d chars from %s", len(text), image_path)
        return text
    except Exception as e:
        logger.error("PaddleOCR error: %s", e)
        return ""


def extract_text_tesseract(image_path: str) -> str:
    """Extract text using pytesseract (Tesseract-OCR).

    Args:
        image_path: Path to the screenshot image.

    Returns:
        Extracted text string, or empty string on failure.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.info("pytesseract not installed (pip install pytesseract).")
        return ""

    if not os.path.isfile(image_path):
        logger.error("Image not found: %s", image_path)
        return ""

    try:
        img = Image.open(image_path)
        # Preprocess: convert to grayscale for better accuracy
        img = img.convert("L")
        text = pytesseract.image_to_string(img, lang="eng")
        text = text.strip()
        logger.info("Tesseract extracted %d chars from %s", len(text), image_path)
        return text
    except Exception as e:
        logger.error("Tesseract error: %s", e)
        return ""


def extract_text(image_path: str, backend: str = "auto") -> str:
    """Extract text from a screenshot image using the best available OCR.

    Args:
        image_path: Path to the image file.
        backend: 'paddle', 'tesseract', or 'auto' (try paddle -> tesseract).

    Returns:
        Extracted text string, or empty string if all backends fail.
    """
    if backend == "paddle":
        return extract_text_paddle(image_path)
    if backend == "tesseract":
        return extract_text_tesseract(image_path)

    # Auto: try PaddleOCR first, then Tesseract
    text = extract_text_paddle(image_path)
    if text:
        return text
    logger.info("PaddleOCR failed — trying pytesseract fallback.")
    return extract_text_tesseract(image_path)
