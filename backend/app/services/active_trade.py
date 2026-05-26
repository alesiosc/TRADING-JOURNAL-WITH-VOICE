"""
Active Trade Tracker — in-memory singleton that tracks the "currently active" trade.

Purpose:
- Screenshots can auto-attach to the active trade when captured.
- Voice commands can operate on the active trade (add leg, modify stop, etc.).
- Active window/instrument context can be tracked for voice disambiguation.

Thread-safe via a threading.Lock.
"""

from __future__ import annotations
import threading
from typing import Optional


class ActiveTradeTracker:
    """
    Singleton in-memory tracker for the currently active trade.

    Usage:
        tracker = ActiveTradeTracker()
        tracker.set_active(trade_id=42, instrument="ES")
        trade_id = tracker.get_active_trade_id()  # -> 42
        instr = tracker.get_active_instrument()   # -> "ES"
        tracker.clear()
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_trade_id: Optional[int] = None
        self._active_instrument: Optional[str] = None
        self._active_window: Optional[str] = None  # e.g. "Thinkorswim - AAPL"

    # ------------------------------------------------------------------
    # Trade ID
    # ------------------------------------------------------------------

    def set_active(self, trade_id: int, instrument: Optional[str] = None) -> None:
        """Mark a trade as the currently active trade."""
        with self._lock:
            self._active_trade_id = trade_id
            if instrument is not None:
                self._active_instrument = instrument

    def get_active_trade_id(self) -> Optional[int]:
        """Return the active trade ID, or None."""
        with self._lock:
            return self._active_trade_id

    # ------------------------------------------------------------------
    # Instrument context
    # ------------------------------------------------------------------

    def set_active_instrument(self, instrument: str) -> None:
        """Set the active instrument context (e.g. from voice parsing)."""
        with self._lock:
            self._active_instrument = instrument

    def get_active_instrument(self) -> Optional[str]:
        """Return the active instrument symbol, or None."""
        with self._lock:
            return self._active_instrument

    # ------------------------------------------------------------------
    # Window context
    # ------------------------------------------------------------------

    def set_active_window(self, window_title: str) -> None:
        """Track the active window title (e.g. for screenshot context)."""
        with self._lock:
            self._active_window = window_title

    def get_active_window(self) -> Optional[str]:
        """Return the active window title."""
        with self._lock:
            return self._active_window

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all active state."""
        with self._lock:
            self._active_trade_id = None
            self._active_instrument = None
            self._active_window = None

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """Whether a trade is currently active."""
        return self.get_active_trade_id() is not None

    def get_status(self) -> dict:
        """Return the full status as a dict."""
        with self._lock:
            return {
                "active_trade_id": self._active_trade_id,
                "active_instrument": self._active_instrument,
                "active_window": self._active_window,
            }


# Module-level singleton
_active_tracker = ActiveTradeTracker()


def get_active_trade_tracker() -> ActiveTradeTracker:
    """Get the singleton ActiveTradeTracker instance."""
    return _active_tracker


# Convenience module-level functions (mirror the class API)
def set_active(trade_id: int, instrument: Optional[str] = None) -> None:
    _active_tracker.set_active(trade_id, instrument)

def get_active() -> Optional[int]:
    return _active_tracker.get_active_trade_id()

def clear_active() -> None:
    _active_tracker.clear()

def get_active_instrument() -> Optional[str]:
    return _active_tracker.get_active_instrument()

def set_active_instrument(instrument: str) -> None:
    _active_tracker.set_active_instrument(instrument)

def get_status() -> dict:
    return _active_tracker.get_status()
