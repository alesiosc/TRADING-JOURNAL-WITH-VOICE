"""
CSV Normalizer — Import trades from any broker CSV format.

This is the most universal connector. Every broker and prop firm exports CSV.
The normalizer detects the format and maps columns to the canonical schema.

Supported formats:
  - NT8 (NinjaTrader 8 TradePerformance)
  - MT4 / MT5 (MetaTrader)
  - Quantower
  - Generic (user-mapped columns)

Usage:
    from brokers.csv_normalizer import CsvNormalizer
    
    normalizer = CsvNormalizer()
    # Auto-detect format
    format_name = normalizer.detect_format("path/to/trades.csv")
    # Parse into canonical trades
    trades = normalizer.parse("path/to/trades.csv")
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import csv
import logging

logger = logging.getLogger("brokers.csv_normalizer")


# Known column signatures for format detection
FORMAT_SIGNATURES = {
    "nt8": [
        "instrument", "symbol", "entry price", "exit price",
        "entry date", "exit date", "profit loss",
    ],
    "mt4": [
        "ticket", "open time", "close time", "symbol",
        "type", "volume", "open price", "close price",
        "sl", "tp", "commission", "swap", "profit",
    ],
    "mt5": [
        "ticket", "open time", "close time", "symbol",
        "type", "volume", "open price", "close price",
        "sl", "tp", "commission", "swap", "profit",
    ],
    "quantower": [
        "symbol", "side", "quantity", "opentime", "closetime",
    ],
}

# Column aliases for generic CSV mapping
COLUMN_ALIASES = {
    "instrument": ["symbol", "ticker", "pair", "asset", "market", "instrument"],
    "direction": ["side", "type", "action", "direction", "buy/sell"],
    "volume": ["qty", "quantity", "size", "shares", "contracts", "lots", "amount", "volume"],
    "entry_price": ["entry price", "entry price", "open price", "open price", "entry", "open"],
    "exit_price": ["exit price", "exit price", "close price", "close price", "exit", "close"],
    "entry_time": ["entry time", "entry datetime", "entry date", "open time", "open datetime", "open date"],
    "exit_time": ["exit time", "exit datetime", "exit date", "close time", "close datetime", "close date"],
    "commission": ["commission", "fee", "fees", "cost"],
    "swap": ["swap", "swap points", "rollover"],
    "pnl": ["profit", "loss", "pnl", "pl", "result", "net pnl", "profit loss"],
    "broker": ["broker", "platform", "source"],
    "notes": ["notes", "note", "comment", "remarks", "description", "journal"],
}


class CsvNormalizer:
    """Detects CSV format and normalizes to canonical trade schema."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def detect_format(self, file_path: str) -> str:
        """Detect the broker format by analyzing column headers."""
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
        except Exception as e:
            logger.warning("Cannot read %s: %s", file_path, e)
            return "generic"

        lower_headers = [h.strip().lower() for h in headers]

        scores = {}
        for fmt, sigs in FORMAT_SIGNATURES.items():
            score = sum(
                1 for sig in sigs
                if any(sig in h for h in lower_headers)
            )
            scores[fmt] = score

        best_format = max(scores, key=scores.get)
        best_score = scores[best_format]

        if best_score >= 3:
            return best_format

        return "generic"

    def parse(self, file_path: str) -> list[dict]:
        """Parse a CSV file and return a list of canonical trade dicts."""
        fmt = self.detect_format(file_path)
        logger.info("Detected format '%s' for %s", fmt, file_path)

        parser_map = {
            "nt8": self._parse_nt8,
            "mt4": self._parse_mt4,
            "mt5": self._parse_mt5,
            "quantower": self._parse_quantower,
            "generic": self._parse_generic,
        }

        parser = parser_map.get(fmt, self._parse_generic)
        return parser(file_path)

    # ------------------------------------------------------------------
    # NT8 TradePerformance parser
    # ------------------------------------------------------------------
    def _parse_nt8(self, file_path: str) -> list[dict]:
        trades = []
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trade = {
                        "broker": "nt8",
                        "broker_trade_id": row.get("Trade ID", ""),
                        "instrument": row.get("Instrument", row.get("Symbol", "")),
                        "direction": "long" if row.get("Direction", "").lower() in ("long", "buy") else "short",
                        "volume": float(row.get("Quantity", row.get("Volume", 0) or 0)),
                        "entry_price": float(row.get("Entry Price", row.get("EntryPrice", 0) or 0)),
                        "exit_price": float(row.get("Exit Price", row.get("ExitPrice", "") or 0) or None),
                        "entry_time": row.get("Entry Date", row.get("EntryDate", "")),
                        "exit_time": row.get("Exit Date", row.get("ExitDate", "")),
                        "pnl": float(row.get("Profit Loss", row.get("ProfitLoss", 0) or 0)),
                        "pnl_pct": None,
                        "commission": float(row.get("Commission", 0) or 0),
                        "swap": 0.0,
                        "strategy_tag": row.get("Strategy Tag", row.get("Strategy", "")),
                        "notes": row.get("Notes", ""),
                        "status": "closed",
                    }
                    trades.append(self._clean_trade(trade))
        except Exception as e:
            logger.error("NT8 parse error: %s", e)
        return trades

    # ------------------------------------------------------------------
    # MT4/5 parser
    # ------------------------------------------------------------------
    def _parse_mt4(self, file_path: str) -> list[dict]:
        trades = []
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    side = row.get("Type", "").lower()
                    trade = {
                        "broker": "mt4",
                        "broker_trade_id": row.get("Ticket", ""),
                        "instrument": row.get("Symbol", ""),
                        "direction": "long" if side in ("buy", "long") else "short",
                        "volume": float(row.get("Volume", row.get("Lots", 0) or 0)),
                        "entry_price": float(row.get("Open Price", row.get("OpenPrice", 0) or 0)),
                        "exit_price": float(row.get("Close Price", row.get("ClosePrice", "") or 0) or None),
                        "entry_time": row.get("Open Time", row.get("OpenTime", "")),
                        "exit_time": row.get("Close Time", row.get("CloseTime", "")),
                        "pnl": float(row.get("Profit", 0) or 0),
                        "pnl_pct": None,
                        "commission": float(row.get("Commission", 0) or 0),
                        "swap": float(row.get("Swap", 0) or 0),
                        "strategy_tag": "",
                        "notes": "",
                        "status": "closed",
                    }
                    trades.append(self._clean_trade(trade))
        except Exception as e:
            logger.error("MT4 parse error: %s", e)
        return trades

    _parse_mt5 = _parse_mt4  # same format

    # ------------------------------------------------------------------
    # Quantower parser
    # ------------------------------------------------------------------
    def _parse_quantower(self, file_path: str) -> list[dict]:
        trades = []
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    side = row.get("Side", row.get("Type", "")).lower()
                    trade = {
                        "broker": "quantower",
                        "broker_trade_id": row.get("Order ID", row.get("Ticket", "")),
                        "instrument": row.get("Symbol", ""),
                        "direction": "long" if side in ("buy", "long") else "short",
                        "volume": float(row.get("Quantity", row.get("Volume", 0) or 0)),
                        "entry_price": float(row.get("Entry Price", row.get("OpenPrice", 0) or 0)),
                        "exit_price": float(row.get("Exit Price", row.get("ClosePrice", "") or 0) or None),
                        "entry_time": row.get("Open Time", row.get("OpenTime", "")),
                        "exit_time": row.get("Close Time", row.get("CloseTime", "")),
                        "pnl": float(row.get("PnL", row.get("Profit", 0) or 0)),
                        "pnl_pct": None,
                        "commission": float(row.get("Commission", 0) or 0),
                        "swap": 0.0,
                        "strategy_tag": "",
                        "notes": "",
                        "status": "closed",
                    }
                    trades.append(self._clean_trade(trade))
        except Exception as e:
            logger.error("Quantower parse error: %s", e)
        return trades

    # ------------------------------------------------------------------
    # Generic CSV parser with column mapping
    # ------------------------------------------------------------------
    def _parse_generic(self, file_path: str) -> list[dict]:
        """Try to parse any CSV by matching column aliases."""
        trades = []
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                # Build a mapping from canonical field -> CSV header
                mapping = {}
                for canonical, aliases in COLUMN_ALIASES.items():
                    for alias in aliases:
                        for h in headers:
                            if h.strip().lower() == alias:
                                mapping[canonical] = h
                                break
                        if canonical in mapping:
                            break

                for row in reader:
                    def get(field, default=""):
                        h = mapping.get(field)
                        return row.get(h, default) if h else default

                    side = get("direction", "long").lower()
                    trade = {
                        "broker": "csv",
                        "broker_trade_id": "",
                        "instrument": get("instrument", ""),
                        "direction": "long" if side in ("buy", "long") else "short",
                        "volume": float(get("volume", 0) or 0),
                        "entry_price": float(get("entry_price", 0) or 0),
                        "exit_price": float(get("exit_price", 0)) if get("exit_price") else None,
                        "entry_time": get("entry_time", ""),
                        "exit_time": get("exit_time", ""),
                        "pnl": float(get("pnl", 0)) if get("pnl") else None,
                        "pnl_pct": None,
                        "commission": float(get("commission", 0) or 0),
                        "swap": float(get("swap", 0) or 0),
                        "strategy_tag": "",
                        "notes": get("notes", ""),
                        "status": "closed",
                    }
                    trades.append(self._clean_trade(trade))

        except Exception as e:
            logger.error("Generic CSV parse error: %s", e)

        return trades

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_trade(trade: dict) -> dict:
        """Clean and validate trade fields."""
        # Strip whitespace from strings
        for k, v in trade.items():
            if isinstance(v, str):
                trade[k] = v.strip()

        # Ensure direction is clean
        if trade.get("direction") not in ("long", "short"):
            trade["direction"] = "long"

        return trade


def normalize_csv(file_path: str, config: Optional[dict] = None) -> list[dict]:
    """Convenience function to normalize a CSV file."""
    normalizer = CsvNormalizer(config)
    return normalizer.parse(file_path)
