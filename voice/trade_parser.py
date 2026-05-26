"""
Trade dictation parser — converts natural language trade descriptions into
structured trade dictionaries.

Examples:
    "long ES 2 contracts at 5032.50, stop at 5018, target 5060"
    -> {
        "direction": "long",
        "symbol": "ES",
        "quantity": 2.0,
        "entry_price": 5032.50,
        "stop_loss": 5018.0,
        "take_profit": 5060.0,
    }

Handles:
    Direction:  buy / sell / long / short / bought / sold
    Symbol:     uppercase ticker / futures code
    Quantity:   with contracts / shares / lots / units
    Entry:      at / @ / entry
    Stop:       stop / SL / stop loss / protection
    Target:     target / TP / take profit / limit
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("voice.trade_parser")

# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

# Direction keywords mapped to canonical values
DIRECTION_MAP = {
    "long": "long",
    "buy": "long",
    "bought": "long",
    "short": "short",
    "sell": "short",
    "sold": "short",
}

# Quantity qualifiers
QUANTITY_WORDS = r"(?:contracts?|shares?|lots?|units?)"
QUANTITY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*" + QUANTITY_WORDS, re.IGNORECASE)

# Entry price patterns
ENTRY_PATTERN = re.compile(
    r"(?:at|@|entry(?:\s+at\s+)?)\s*(\d+(?:[,.]\d+)?)",
    re.IGNORECASE,
)

# Stop loss patterns
STOP_PATTERN = re.compile(
    r"(?:stop(?:\s+loss)?|sl|protection)\s*(?:at\s*)?(\d+(?:[,.]\d+)?)",
    re.IGNORECASE,
)

# Take-profit / target patterns
TAKEPROFIT_PATTERN = re.compile(
    r"(?:target|tp|take\s*profit|limit)\s*(?:at\s*)?(\d+(?:[,.]\d+)?)",
    re.IGNORECASE,
)

# Symbol pattern — first capitalized/uppercase word after the direction
SYMBOL_PATTERN = re.compile(
    r"(?:long|short|buy|sell|bought|sold)\s+([A-Za-z0-9/_#.]+)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Clean helpers
# ---------------------------------------------------------------------------

def _clean_number(s: str) -> float:
    """Convert a string number (possibly with commas) to float."""
    return float(s.replace(",", ""))


def _find_direction(text: str) -> Optional[str]:
    """Extract trade direction from the text."""
    tokens = text.lower().split()
    for t in tokens:
        if t in DIRECTION_MAP:
            return DIRECTION_MAP[t]
    return None


def _find_symbol(text: str, direction: str) -> str:
    """Extract symbol after the direction keyword."""
    m = SYMBOL_PATTERN.search(text)
    if m:
        return m.group(1).upper()
    # Try fallback: first word that is all-uppercase or title-cased
    for word in text.split():
        clean = word.strip(",.!?;:")
        if clean.isupper() and len(clean) > 1 and not clean.isdigit():
            return clean
    return ""


def _find_quantity(text: str) -> float:
    """Extract quantity from text."""
    m = QUANTITY_PATTERN.search(text)
    if m:
        return float(m.group(1))
    # Fallback: look for a standalone number before a qualifier
    m = re.search(r"(\d+(?:\.\d+)?)\s*$", text.split("at")[0] if "at" in text.lower() else text)
    if m:
        return float(m.group(1))
    return 1.0  # default to 1


def _find_entry_price(text: str) -> float:
    """Extract entry price from text."""
    m = ENTRY_PATTERN.search(text)
    if m:
        return _clean_number(m.group(1))
    return 0.0


def _find_stop_loss(text: str) -> Optional[float]:
    """Extract stop loss from text."""
    m = STOP_PATTERN.search(text)
    if m:
        return _clean_number(m.group(1))
    return None


def _find_take_profit(text: str) -> Optional[float]:
    """Extract take profit / target from text."""
    m = TAKEPROFIT_PATTERN.search(text)
    if m:
        return _clean_number(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse(text: str) -> Optional[dict]:
    """Parse a natural language trade dictation into a structured dictionary.

    Args:
        text: Natural language trade description string.

    Returns:
        dict with keys: direction, symbol, quantity, entry_price,
        stop_loss, take_profit, raw_text.
        Returns None if direction cannot be determined.
    """
    if not text or not text.strip():
        return None

    text_clean = text.strip()
    direction = _find_direction(text_clean)
    if not direction:
        logger.warning("Could not detect trade direction in: %s", text_clean[:80])
        return None

    result = {
        "direction": direction,
        "symbol": _find_symbol(text_clean, direction),
        "quantity": _find_quantity(text_clean),
        "entry_price": _find_entry_price(text_clean),
        "stop_loss": _find_stop_loss(text_clean),
        "take_profit": _find_take_profit(text_clean),
        "raw_text": text_clean,
    }

    logger.info(
        "Parsed trade: %s %s %s @ %.2f SL=%.2f TP=%.2f",
        result["direction"],
        result["quantity"],
        result["symbol"],
        result["entry_price"],
        result["stop_loss"] or 0,
        result["take_profit"] or 0,
    )
    return result


def parse_batch(texts: list[str]) -> list[Optional[dict]]:
    """Parse multiple trade descriptions at once."""
    return [parse(t) for t in texts]
