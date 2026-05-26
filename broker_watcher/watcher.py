"""
Broker CSV Auto-Watcher — PollingWatcher engine.

Timer-based polling that monitors broker export directories for new CSV
files and auto-imports them into the Trading Journal via the backend API.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger("broker_watcher")


# ---------------------------------------------------------------------------
# Broker-format detection helpers
# ---------------------------------------------------------------------------

# Known NT8 TradePerformance columns (case-insensitive prefix matching)
NT8_SIGNATURES = [
    "instrument",
    "symbol",
    "entry price",
    "exit price",
    "entry date",
    "exit date",
    "profit loss",
    "commission",
    "quantity",
    "direction",
    "trade type",
]

MT4_SIGNATURES = [
    "ticket",
    "open time",
    "close time",
    "symbol",
    "type",
    "volume",
    "open price",
    "close price",
    "sl",
    "tp",
    "commission",
    "swap",
    "profit",
]

MT5_SIGNATURES = MT4_SIGNATURES  # mostly identical format


def detect_broker_format(headers: List[str]) -> str:
    """Detect the broker format from CSV header names.

    Returns one of: 'nt8', 'mt4', 'mt5', 'quantower', 'generic'
    """
    lower_headers = [h.strip().lower() for h in headers]

    # NT8 check — look for "trade performance" style columns
    nt8_score = sum(1 for sig in NT8_SIGNATURES if any(sig in h for h in lower_headers))
    mt4_score = sum(1 for sig in MT4_SIGNATURES if any(sig in h for h in lower_headers))

    # Quantower: often has columns like "Symbol", "Side", "Quantity", "OpenTime"
    quantower_score = sum(
        1 for kw in ["symbol", "side", "quantity", "opentime", "closetime"]
        if any(kw in h for h in lower_headers)
    )

    scores = {
        "nt8": nt8_score,
        "mt4": mt4_score,
        "quantower": quantower_score,
    }
    best = max(scores, key=scores.get)
    if scores[best] >= 3:
        return best
    return "generic"


def generate_broker_tag(broker: str) -> Optional[str]:
    """Return a tag string for the detected broker."""
    mapping = {
        "nt8": "broker:nt8",
        "mt4": "broker:mt4",
        "mt5": "broker:mt5",
        "quantower": "broker:quantower",
    }
    return mapping.get(broker)


# ---------------------------------------------------------------------------
# State file helper — track already-seen files across restarts
# ---------------------------------------------------------------------------

STATE_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / ".watcher_state.json"


def _load_state() -> dict:
    """Load the file-tracking state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"seen": {}}


def _save_state(state: dict) -> None:
    """Persist the file-tracking state to disk."""
    try:
        STATE_FILE.write_text(
            json.dumps(state, indent=2, default=str), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("Could not write state file: %s", exc)


# ---------------------------------------------------------------------------
# PollingWatcher
# ---------------------------------------------------------------------------


class PollingWatcher:
    """Timer-based watcher that polls configured directories for new CSV files.

    When a new or modified CSV is detected, it:
      1. Detects the broker format from column headers.
      2. POSTs the file to the backend import API.
      3. On success, optionally moves the file to an ``_imported/`` subdirectory.
      4. Broadcasts results via the provided callback (e.g. WebSocket broadcast).
    """

    def __init__(
        self,
        config: dict,
        on_import_result: Optional[Callable] = None,
    ):
        self.config = config
        self.on_import_result = on_import_result
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._lock = threading.Lock()
        self._state = _load_state()

        # Resolve any glob-style patterns in watch_dirs (e.g. MetaQuotes wildcards)
        self._resolved_dirs = self._resolve_watch_dirs()

        # Compile the file-matching pattern
        raw_pattern = config.get("pattern", "*.csv")
        self._file_regex = re.compile(
            "^" + raw_pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".") + "$",
            re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Directory resolution
    # ------------------------------------------------------------------

    def _resolve_watch_dirs(self) -> List[str]:
        """Expand glob patterns (``*``) in watch directory paths.

        Handles cases like::

            C:/Users/.../MetaQuotes/Terminal/*/MQL4/Files/

        by expanding the wildcard to actual terminal directories.
        """
        raw_dirs = self.config.get("watch_dirs", [])
        resolved: List[str] = []
        for d in raw_dirs:
            if "*" in d:
                # Expand the first glob segment only (safest)
                parts = d.replace("\\", "/").split("/")
                expanded = False
                for i, part in enumerate(parts):
                    if "*" in part:
                        prefix = "/".join(parts[:i])
                        suffix = "/".join(parts[i + 1:])
                        candidates = list(Path(prefix).glob(part))
                        for cand in candidates:
                            combined = str(cand / suffix)
                            if combined not in resolved:
                                resolved.append(combined)
                        expanded = True
                        break
                if not expanded:
                    resolved.append(d)
            else:
                if d not in resolved:
                    resolved.append(d)
        return resolved

    @staticmethod
    def _load_config(path: Optional[str] = None) -> dict:
        """Load the YAML config file (using a simple parser to avoid pyyaml dep)."""
        import yaml  # lazy import — available in most environments
        config_path = path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.yaml"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin polling in a background timer loop."""
        with self._lock:
            if self._running:
                logger.info("Watcher already running.")
                return
            self._running = True
            logger.info(
                "Broker watcher started — polling %d director(ies) every %ds",
                len(self._resolved_dirs),
                self.config.get("poll_interval_seconds", self.config.get("poll_interval", 30)),
            )
        self._tick()

    def stop(self) -> None:
        """Stop the polling loop."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        logger.info("Broker watcher stopped.")

    def toggle(self) -> bool:
        """Toggle between running and stopped. Returns the new state."""
        if self._running:
            self.stop()
            return False
        else:
            self.start()
            return True

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """One poll iteration: scan all directories and schedule next tick."""
        if not self._running:
            return

        try:
            self._poll_once()
        except Exception as exc:
            logger.exception("Error during poll cycle: %s", exc)

        interval = self.config.get(
            "poll_interval_seconds",
            self.config.get("poll_interval", 30),
        )
        with self._lock:
            if self._running:
                self._timer = threading.Timer(interval, self._tick)
                self._timer.daemon = True
                self._timer.start()

    def _poll_once(self) -> None:
        """Scan all resolved directories for new / modified CSV files."""
        if not self.config.get("enabled", True):
            return

        auto_import = self.config.get("auto_import", True)
        if not auto_import:
            return

        for watch_dir in self._resolved_dirs:
            dir_path = Path(watch_dir)
            if not dir_path.is_dir():
                continue

            try:
                for entry in dir_path.iterdir():
                    if not entry.is_file():
                        continue
                    if not self._file_regex.match(entry.name):
                        continue
                    self._process_file(entry)
            except PermissionError:
                logger.warning("Permission denied reading: %s", watch_dir)
            except OSError as exc:
                logger.warning("Error scanning %s: %s", watch_dir, exc)

    # ------------------------------------------------------------------
    # File processing
    # ------------------------------------------------------------------

    def _process_file(self, file_path: Path) -> None:
        """Check if *file_path* is new or changed, then import it."""
        # Use absolute path as seen key
        abs_path = str(file_path.resolve())
        current_mtime = file_path.stat().st_mtime

        seen = self._state.setdefault("seen", {})
        prev_mtime = seen.get(abs_path)

        # Skip if already seen with the same mtime
        if prev_mtime is not None and abs(prev_mtime - current_mtime) < 0.001:
            return

        logger.info("New / modified CSV detected: %s", abs_path)

        # Mark as seen *before* processing to avoid re-processing
        # even if processing fails
        seen[abs_path] = current_mtime
        _save_state(self._state)

        # Process the file
        self._import_file(file_path)

    def _import_file(self, file_path: Path) -> None:
        """Read the CSV, POST it to the backend, and handle the result."""
        try:
            raw = file_path.read_bytes()
        except OSError as exc:
            logger.error("Cannot read %s: %s", file_path, exc)
            self._emit_result({"file": str(file_path), "status": "error", "error": str(exc)})
            return

        # Upload to backend via HTTP
        result = self._upload_to_backend(file_path.name, raw)

        if result.get("status") == "ok":
            logger.info(
                "Imported %s — %d trades, %d errors",
                file_path.name,
                result.get("success_count", 0),
                result.get("error_count", 0),
            )

            # Move imported file if configured
            if self.config.get("move_imported", True):
                self._move_file(file_path)

        else:
            logger.warning("Import failed for %s: %s", file_path.name, result.get("error", "unknown"))

        self._emit_result(result)

    def _upload_to_backend(self, filename: str, data: bytes) -> dict:
        """POST a CSV file to the backend import API.

        Returns a result dict::

            {"status": "ok" | "error", "file": ..., "success_count": N,
             "error_count": N, "errors": [...], "rows": [...]}
        """
        api_base = self.config.get("api_base_url", "http://localhost:8000")
        endpoint = self.config.get("api_import_endpoint", "/api/import/csv")
        url = f"{api_base.rstrip('/')}{endpoint}"

        dry_run = self.config.get("dry_run_first", True)

        try:
            import requests  # lazy import
        except ImportError:
            return {
                "status": "error",
                "file": filename,
                "error": "`requests` library not installed. Run: pip install requests",
            }

        try:
            resp = requests.post(
                url,
                files={"file": (filename, data, "text/csv")},
                params={"dry_run": str(dry_run).lower()},
                timeout=(5, 30),  # (connect, read) seconds
            )
            resp.raise_for_status()
            payload = resp.json()
            return {
                "status": "ok",
                "file": filename,
                "success_count": payload.get("success_count", 0),
                "error_count": payload.get("error_count", 0),
                "errors": payload.get("errors", []),
                "rows": payload.get("rows", []),
                "total_rows": payload.get("total_rows", 0),
                "dry_run": dry_run,
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "file": filename,
                "error": f"Cannot reach backend at {api_base}. Is the server running?",
            }
        except requests.exceptions.RequestException as exc:
            return {
                "status": "error",
                "file": filename,
                "error": str(exc),
            }

    def _move_file(self, file_path: Path) -> None:
        """Move the file into an ``_imported/`` subfolder next to it."""
        dest_dir = file_path.parent / "_imported"
        dest_dir.mkdir(exist_ok=True)
        # Timestamp the filename to avoid collisions
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"{file_path.stem}_{ts}{file_path.suffix}"
        dest = dest_dir / dest_name
        try:
            shutil.move(str(file_path), str(dest))
            logger.info("Moved %s -> %s", file_path.name, dest)
        except OSError as exc:
            logger.warning("Could not move %s: %s", file_path.name, exc)

    def _emit_result(self, result: dict) -> None:
        """Pass the result dict to the optional callback."""
        if self.on_import_result:
            try:
                self.on_import_result(result)
            except Exception as exc:
                logger.exception("Import result callback failed: %s", exc)


# ---------------------------------------------------------------------------
# Convenience: run standalone
# ---------------------------------------------------------------------------

def run_standalone(config_path: Optional[str] = None):
    """Run the watcher as a standalone script (blocking)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config = PollingWatcher._load_config(config_path)

    # Set up file logging if configured
    log_file = config.get("log_file")
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        logging.getLogger().addHandler(fh)

    watcher = PollingWatcher(config)

    def signal_handler(signum, frame):
        logger.info("Received signal — shutting down.")
        watcher.stop()

    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    watcher.start()
    logger.info("Broker watcher running. Press Ctrl+C to stop.")
    try:
        while watcher.running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        logger.info("Broker watcher shut down.")


if __name__ == "__main__":
    run_standalone()
