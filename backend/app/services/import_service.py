"""
CSV import service for the Trading Journal.
Parses common trading journal CSV formats and returns validated trade dicts.
"""

import csv
import re
from io import StringIO
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models import Instrument


# Column name mapping: (canonical_name, [possible_headers])
COLUMN_MAP = {
    "symbol": ["instrument", "symbol", "ticker", "pair", "market"],
    "direction": ["direction", "type", "buy_sell", "side", "action", "signal"],
    "volume": ["volume", "shares", "quantity", "qty", "size", "amount"],
    "entry_price": ["entry", "entry_price", "entryprice", "open_price", "openprice", "buy_price"],
    "exit_price": ["exit", "exit_price", "exitprice", "close_price", "closeprice", "sell_price"],
    "entry_time": ["entry_date", "entry_time", "entrydate", "entrytime", "date_open", "dateopen", "open_date", "opendate"],
    "exit_time": ["exit_date", "exit_time", "exitdate", "exittime", "date_close", "dateclose", "close_date", "closedate"],
    "pnl": ["pnl", "profit_loss", "profitloss", "net_pnl", "netpnl", "pl", "p&l"],
    "commission": ["commission", "fees", "commission", "fee"],
    "sl": ["sl", "stoploss", "stop_loss", "stoplos", "stop"],
    "tp": ["tp", "takeprofit", "take_profit", "takeprof", "target"],
    "strategy": ["strategy", "strategy_tag", "strategy_tag", "system"],
    "notes": ["notes", "comment", "comments", "note", "description"],
    "rating": ["rating", "score", "stars"],
}


def _normalize_header(h: str) -> str:
    """Normalize a header string: lowercase, strip, remove underscores/spaces."""
    return h.strip().lower().replace(" ", "_").replace("-", "_")


def _resolve_column(header: str) -> Optional[str]:
    """Map a raw CSV header to a canonical column name."""
    norm = _normalize_header(header)
    for canonical, aliases in COLUMN_MAP.items():
        if norm == canonical or norm in aliases:
            return canonical
    return None


def _parse_datetime(value: str) -> Optional[datetime]:
    """Try multiple datetime formats."""
    if not value or not value.strip():
        return None
    value = value.strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%m-%d-%Y %H:%M:%S",
        "%m-%d-%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _parse_float(value: str) -> Optional[float]:
    """Parse a float, handling various formats."""
    if not value or not value.strip():
        return None
    # Remove currency symbols and commas
    cleaned = value.strip().replace("$", "").replace("€", "").replace("£", "").replace(",", "")
    # Handle parentheses for negatives: (123.45) -> -123.45
    match = re.match(r"^\((.+)\)$", cleaned)
    if match:
        cleaned = "-" + match.group(1)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _map_direction(value: str) -> str:
    """Map direction strings to 'long' or 'short'."""
    v = value.strip().lower()
    if v in ("long", "buy", "b", "bull", "bullish"):
        return "long"
    if v in ("short", "sell", "s", "bear", "bearish", "sh"):
        return "short"
    return v  # return as-is


def parse_csv(content: str, db: Session) -> dict:
    """
    Parse raw CSV content and return validated rows.

    Returns:
        {
            "success": [list of trade_create dicts],
            "errors": [{"row": int, "reason": str}]
        }
    """
    result = {"success": [], "errors": []}

    try:
        reader = csv.DictReader(StringIO(content))
    except Exception as e:
        result["errors"].append({"row": 0, "reason": f"Failed to parse CSV: {str(e)}"})
        return result

    if not reader.fieldnames:
        result["errors"].append({"row": 0, "reason": "Empty CSV or no headers found"})
        return result

    # Map headers
    header_map = {}  # raw_header -> canonical_name
    for h in reader.fieldnames:
        canonical = _resolve_column(h)
        if canonical:
            header_map[h] = canonical

    # Check for required columns
    required = ["symbol", "entry_price"]
    missing = [r for r in required if r not in header_map.values()]
    if missing:
        result["errors"].append({
            "row": 0,
            "reason": f"Missing required columns: {', '.join(missing)}. Found headers: {', '.join(reader.fieldnames)}",
        })
        return result

    for row_idx, row in enumerate(reader, start=2):  # 1-indexed, row 1 is header
        try:
            trade_dict = _process_row(row, row_idx, header_map, db)
            if "error" in trade_dict:
                result["errors"].append({"row": row_idx, "reason": trade_dict["error"]})
            else:
                result["success"].append(trade_dict)
        except Exception as e:
            result["errors"].append({"row": row_idx, "reason": f"Unexpected error: {str(e)}"})

    return result


def _process_row(row: dict, row_idx: int, header_map: dict, db: Session) -> dict:
    """Process a single CSV row into a trade create dict."""
    trade = {}

    # Symbol / Instrument
    raw_sym = None
    for raw_h, canonical in header_map.items():
        if canonical == "symbol":
            raw_sym = row.get(raw_h, "").strip()
            break
    if not raw_sym:
        return {"error": "Missing instrument symbol"}

    # Look up or create instrument
    instr = db.query(Instrument).filter(Instrument.symbol == raw_sym).first()
    if not instr:
        instr = Instrument(symbol=raw_sym, name=raw_sym)
        db.add(instr)
        db.flush()
    trade["instrument_id"] = instr.id

    # Direction (default to long)
    direction = "long"
    for raw_h, canonical in header_map.items():
        if canonical == "direction":
            val = row.get(raw_h, "").strip()
            if val:
                direction = _map_direction(val)
            break
    trade["direction"] = direction

    # Volume (default to 1.0)
    volume = 1.0
    for raw_h, canonical in header_map.items():
        if canonical == "volume":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None and val > 0:
                volume = val
                break
    trade["volume"] = volume

    # Entry Price
    entry_price = None
    for raw_h, canonical in header_map.items():
        if canonical == "entry_price":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None:
                entry_price = val
                break
    if entry_price is None:
        return {"error": "Missing or invalid entry_price"}
    trade["entry_price"] = entry_price

    # Exit Price (optional)
    for raw_h, canonical in header_map.items():
        if canonical == "exit_price":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None:
                trade["exit_price"] = val
            break

    # Entry Time
    for raw_h, canonical in header_map.items():
        if canonical == "entry_time":
            val = row.get(raw_h, "").strip()
            if val:
                dt = _parse_datetime(val)
                if dt:
                    trade["entry_time"] = dt.isoformat()
            break

    # Exit Time
    for raw_h, canonical in header_map.items():
        if canonical == "exit_time":
            val = row.get(raw_h, "").strip()
            if val:
                dt = _parse_datetime(val)
                if dt:
                    trade["exit_time"] = dt.isoformat()
            break

    # PnL (optional)
    for raw_h, canonical in header_map.items():
        if canonical == "pnl":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None:
                trade["pnl"] = val
            break

    # Commission
    for raw_h, canonical in header_map.items():
        if canonical == "commission":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None:
                trade["commission"] = val
            break

    # Compute status from exit_price presence
    if "exit_price" in trade and trade["exit_price"] is not None:
        trade["status"] = "closed"
    else:
        trade["status"] = "open"

    # Strategy tag
    for raw_h, canonical in header_map.items():
        if canonical == "strategy":
            val = row.get(raw_h, "").strip()
            if val:
                trade["strategy_tag"] = val
            break

    # Notes
    for raw_h, canonical in header_map.items():
        if canonical == "notes":
            val = row.get(raw_h, "").strip()
            if val:
                trade["notes"] = val
            break

    # Rating
    for raw_h, canonical in header_map.items():
        if canonical == "rating":
            val = _parse_float(row.get(raw_h, ""))
            if val is not None and 1 <= val <= 5:
                trade["rating"] = int(val)
            break

    # SL/TP stored via tags
    tags = []
    for raw_h, canonical in header_map.items():
        if canonical == "sl":
            val = row.get(raw_h, "").strip()
            if val:
                tags.append(f"SL:{val}")
        if canonical == "tp":
            val = row.get(raw_h, "").strip()
            if val:
                tags.append(f"TP:{val}")
    if tags:
        trade["_tags"] = tags

    return trade
