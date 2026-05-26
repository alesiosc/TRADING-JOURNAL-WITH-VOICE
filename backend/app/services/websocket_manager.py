"""
WebSocket connection manager for broadcasting trade events to connected clients.
"""

import json
from typing import Set, Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to all clients."""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected clients."""
        dead = set()
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.connections.discard(ws)

    @property
    def count(self) -> int:
        return len(self.connections)


# Singleton instance
manager = ConnectionManager()
