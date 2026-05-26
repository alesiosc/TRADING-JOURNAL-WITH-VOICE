"""
Broker CSV Auto-Watcher
=======================

Monitors NT8 / MT4 / MT5 / Quantower export folders for new CSV trade
export files and auto-imports them into the Trading Journal.

Quick start::

    from broker_watcher import BrokerWatcher

    watcher = BrokerWatcher()
    watcher.start()
    ...
    watcher.stop()

Or from the command line::

    python -m broker_watcher
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, Optional

from broker_watcher.watcher import PollingWatcher, run_standalone

logger = logging.getLogger("broker_watcher")


class BrokerWatcher:
    """Configurable broker CSV auto-watcher with start / stop / toggle.

    Wraps :class:`PollingWatcher` and provides convenience access to
    configuration and status.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config: Optional[dict] = None,
        on_import_result: Optional[Callable] = None,
    ):
        """
        Args:
            config_path: Path to ``config.yaml``. If omitted, looks for it
                next to this file.
            config: Inline dict config. If given, *config_path* is ignored.
            on_import_result: Optional callback ``callable(result_dict)``
                invoked after each file is processed. The result dict
                contains ``status``, ``file``, ``success_count``, etc.
        """
        if config is not None:
            self._config = config
        else:
            cfg_path = config_path or str(
                Path(os.path.dirname(os.path.abspath(__file__))) / "config.yaml"
            )
            self._config = PollingWatcher._load_config(cfg_path)

        self._watcher = PollingWatcher(
            config=self._config,
            on_import_result=on_import_result,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin watching directories."""
        self._watcher.start()

    def stop(self) -> None:
        """Stop watching."""
        self._watcher.stop()

    def toggle(self) -> bool:
        """Toggle between running and stopped. Returns the new running state."""
        return self._watcher.toggle()

    @property
    def running(self) -> bool:
        """Whether the watcher is currently active."""
        return self._watcher.running

    @property
    def config(self) -> dict:
        """The active configuration dict."""
        return dict(self._config)

    def reload_config(self, config_path: Optional[str] = None) -> None:
        """Reload configuration from disk. Restarts the watcher if running."""
        was_running = self._watcher.running
        if was_running:
            self._watcher.stop()

        cfg_path = config_path or str(
            Path(os.path.dirname(os.path.abspath(__file__))) / "config.yaml"
        )
        self._config = PollingWatcher._load_config(cfg_path)
        self._watcher = PollingWatcher(
            config=self._config,
            on_import_result=self._watcher.on_import_result,
        )

        if was_running:
            self._watcher.start()
