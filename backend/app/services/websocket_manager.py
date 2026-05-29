"""
WebSocket manager — currently disabled in stripped-down version.
Provides a no-op broadcast() so existing router imports don't break.
"""

import logging

logger = logging.getLogger(__name__)


class _NoopManager:
    """Placeholder that silently discards broadcast calls."""

    async def broadcast(self, message: dict):
        pass

    async def connect(self, websocket):
        pass

    def disconnect(self, websocket):
        pass


manager = _NoopManager()
