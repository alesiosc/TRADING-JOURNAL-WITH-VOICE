"""
Voice Trade Parser — converts natural speech into structured trade data.

Uses regex patterns only (no LLM). Fast, local, deterministic.
Supports: new_trade, close_trade, add_leg, modify_stop, modify_target intents.
"""

from __future__ import annotations
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Pattern definitions  (order matters — specific before general)
# ---------------------------------------------------------------------------

# Direction keywords
_DIRECTION_PAT = r"(?P<direction>long|short|buy|sell)"

# Volume words: "2 contracts", "5 shares", "0.5 lots", "1000 units", or bare number
_VOLUME_CAPTURE = r"(?P<volume>\d+(?:\.\d+)?)\s*(?:contracts?|shares?|lots?|units?|coins?|btc|eth|usd)?"
_VOLUME_OPT = rf"(?:{_VOLUME_CAPTURE}\s+)?"

# Price pattern: "at 1234.50", "at 1234", "1234.50"
_PRICE_PAT = r"(?:at\s+)?(?P<price>\d+(?:\.\d+)?)"

# Instrument symbol: 1-10 letters, optionally with / (forex) or numbers
_INSTR_CAPTURE = r"(?P<instrument>[A-Za-z]{1,10}(?:/[A-Za-z]{2,10})?(?:\d{1,4})?)"

# Stop / target legs
_STOP_PAT = r"(?:stop\s+(?:loss\s+)?(?:at\s+)?)\s*(?P<stop_price>\d+(?:\.\d+)?)"
_TARGET_PAT = r"(?:target|tp|take\s+profit|limit)(?:\s+at\s+)?\s*(?P<target_price>\d+(?:\.\d+)?)"

# Optional legs suffix (stop and/or target)
_LEGS_SUFFIX = rf"(?:[,;]\s*{_STOP_PAT})?(?:[,;]\s*{_TARGET_PAT})?\s*$"

# ---------------------------------------------------------------------------
# Intent 1a: "long ES 2 contracts at 5032.50, stop at 5028, target 5045"
#           Pattern: direction + instrument + volume + at price [+ legs]
# ---------------------------------------------------------------------------
_NEW_TRADE_INSTR_FIRST_RE = re.compile(
    rf"^{_DIRECTION_PAT}\s+"
    rf"(?:of\s+)?{_INSTR_CAPTURE}\s+"
    rf"{_VOLUME_OPT}?"
    rf"{_PRICE_PAT}"
    rf"{_LEGS_SUFFIX}",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 1b: "buy 1000 shares of AAPL at 220"
#           Pattern: direction + volume + of? instrument + at price [+ legs]
# ---------------------------------------------------------------------------
_NEW_TRADE_VOL_FIRST_RE = re.compile(
    rf"^{_DIRECTION_PAT}\s+"
    rf"{_VOLUME_CAPTURE}\s+"
    rf"(?:of\s+)?{_INSTR_CAPTURE}\s+"
    rf"{_PRICE_PAT}"
    rf"{_LEGS_SUFFIX}",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 1c: "long ES at 5032.50" (no volume, no legs)
#           "short NQ at 18500, stop at 18600, target 18300"
# ---------------------------------------------------------------------------
_NEW_TRADE_NO_VOL_RE = re.compile(
    rf"^{_DIRECTION_PAT}\s+"
    rf"{_INSTR_CAPTURE}\s+"
    rf"{_PRICE_PAT}"
    rf"{_LEGS_SUFFIX}",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 2: "close ES at 5040"
#          "close my ES trade"
# ---------------------------------------------------------------------------
_CLOSE_TRADE_RE = re.compile(
    rf"^close\s+(?:my\s+|the\s+)?(?:trade\s+)?{_INSTR_CAPTURE}"
    rf"(?:\s+(?:at\s+)?(?P<close_price>\d+(?:\.\d+)?))?"
    rf"\s*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 3: "add 1 more NQ at 18450"
#          "add another contract for NQ at 18450"
# ---------------------------------------------------------------------------
_ADD_LEG_RE = re.compile(
    rf"^add\s+"
    rf"(?:{_VOLUME_CAPTURE}\s+)?"
    rf"(?:more\s+|another\s+(?:contract\s+)?)?"
    rf"(?:of\s+)?{_INSTR_CAPTURE}"
    rf"(?:\s+(?:at\s+)?{_PRICE_PAT})?"
    rf"\s*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 4: "move stop on ES to 5025"
#          "move stop loss ES to 5025"
#          "set stop on ES at 5025"
# ---------------------------------------------------------------------------
_MODIFY_STOP_RE = re.compile(
    rf"^(?:move|set|change|update)\s+"
    rf"(?:stop\s+(?:loss\s+)?)"
    rf"(?:on\s+|for\s+)?{_INSTR_CAPTURE}"
    rf"(?:\s+(?:to|at)\s+)(?P<stop_price>\d+(?:\.\d+)?)"
    rf"\s*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Intent 5: "move target on ES to 5050"
#          "set target for NQ at 18600"
# ---------------------------------------------------------------------------
_MODIFY_TARGET_RE = re.compile(
    rf"^(?:move|set|change|update)\s+"
    rf"(?:target|tp|take\s+profit|limit)\s+"
    rf"(?:on\s+|for\s+)?{_INSTR_CAPTURE}"
    rf"(?:\s+(?:to|at)\s+)(?P<target_price>\d+(?:\.\d+)?)"
    rf"\s*$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _normalize_direction(direction: str) -> str:
    """Convert 'buy'/'sell' to 'long'/'short'."""
    d = direction.strip().lower()
    if d in ("buy", "long"):
        return "long"
    if d in ("sell", "short"):
        return "short"
    return d


def _clean_group(match, name: str) -> Optional[str]:
    """Return a matched group or None."""
    val = match.group(name)
    return val.strip() if val else None


def _build_new_trade_from_match(m: re.Match, text: str) -> dict:
    """Build a new_trade result dict from a matched regex."""
    direction = _normalize_direction(_clean_group(m, "direction") or "long")
    instrument = _clean_group(m, "instrument") or ""
    instrument = instrument.upper()
    volume_str = _clean_group(m, "volume")
    volume = float(volume_str) if volume_str else 1.0
    entry_price = float(_clean_group(m, "price"))

    legs = []
    stop_price = _clean_group(m, "stop_price")
    if stop_price:
        legs.append({"type": "stop", "price": float(stop_price)})
    target_price = _clean_group(m, "target_price")
    if target_price:
        legs.append({"type": "target", "price": float(target_price)})

    return {
        "success": True,
        "intent": "new_trade",
        "instrument": instrument,
        "direction": direction,
        "volume": volume,
        "entry_price": entry_price,
        "legs": legs,
        "raw_text": text,
        "notes": None,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_voice_text(text: str) -> dict:
    """
    Parse natural-language trade voice input into a structured dict.

    Returns:
        {
            "success": True,
            "intent": "new_trade" | "close_trade" | "add_leg" | "modify_stop" | "modify_target",
            "instrument": "ES",
            "direction": "long" | "short",        # only for new_trade
            "volume": 2.0,                         # only for new_trade, add_leg
            "entry_price": 5032.5,                 # only for new_trade
            "close_price": 5040.0,                # only for close_trade
            "legs": [{"type": "stop", "price": 5028.0}, ...],  # for new_trade
            "raw_text": "long ES ...",
            "notes": None,
        }

    On failure:
        {
            "success": False,
            "intent": "unknown",
            "raw_text": text,
            "notes": text,    # pass through as notes for manual entry
        }
    """
    text = text.strip()

    # ---- Intent 1: New Trade (try all three patterns) ----
    for pat in [_NEW_TRADE_INSTR_FIRST_RE, _NEW_TRADE_VOL_FIRST_RE, _NEW_TRADE_NO_VOL_RE]:
        m = pat.match(text)
        if m:
            # Validate we got a price
            if _clean_group(m, "price"):
                return _build_new_trade_from_match(m, text)

    # ---- Intent 2: Close Trade ----
    m = _CLOSE_TRADE_RE.match(text)
    if m:
        instrument = _clean_group(m, "instrument") or ""
        instrument = instrument.upper()
        close_price = _clean_group(m, "close_price")
        return {
            "success": True,
            "intent": "close_trade",
            "instrument": instrument,
            "close_price": float(close_price) if close_price else None,
            "raw_text": text,
            "notes": None,
        }

    # ---- Intent 3: Add Leg ----
    m = _ADD_LEG_RE.match(text)
    if m:
        instrument = _clean_group(m, "instrument") or ""
        instrument = instrument.upper()
        volume_str = _clean_group(m, "volume")
        volume = float(volume_str) if volume_str else 1.0
        price = _clean_group(m, "price")
        return {
            "success": True,
            "intent": "add_leg",
            "instrument": instrument,
            "volume": volume,
            "entry_price": float(price) if price else None,
            "raw_text": text,
            "notes": None,
        }

    # ---- Intent 4: Modify Stop ----
    m = _MODIFY_STOP_RE.match(text)
    if m:
        instrument = _clean_group(m, "instrument") or ""
        instrument = instrument.upper()
        stop_price = float(_clean_group(m, "stop_price"))
        return {
            "success": True,
            "intent": "modify_stop",
            "instrument": instrument,
            "stop_price": stop_price,
            "raw_text": text,
            "notes": None,
        }

    # ---- Intent 5: Modify Target ----
    m = _MODIFY_TARGET_RE.match(text)
    if m:
        instrument = _clean_group(m, "instrument") or ""
        instrument = instrument.upper()
        target_price = float(_clean_group(m, "target_price"))
        return {
            "success": True,
            "intent": "modify_target",
            "instrument": instrument,
            "target_price": target_price,
            "raw_text": text,
            "notes": None,
        }

    # ---- Fallback ----
    return {
        "success": False,
        "intent": "unknown",
        "raw_text": text,
        "notes": text,
    }
