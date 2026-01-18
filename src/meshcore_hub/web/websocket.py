"""WebSocket manager for real-time message updates."""

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.debug(f"WebSocket connected. Total connections: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        async with self._lock:
            self._connections.discard(websocket)
        logger.debug(f"WebSocket disconnected. Total connections: {len(self._connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to send
        """
        if not self._connections:
            return

        message_json = json.dumps(message)
        disconnected: set[WebSocket] = set()

        # Get a snapshot of connections to avoid lock contention during broadcast
        async with self._lock:
            connections = self._connections.copy()

        for connection in connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(connection)

        # Remove disconnected connections
        if disconnected:
            async with self._lock:
                self._connections -= disconnected

    async def broadcast_new_message(self, message_data: dict[str, Any]) -> None:
        """Broadcast a new message event to all connected clients.

        Args:
            message_data: Full message data from API
        """
        await self.broadcast({"type": "new_message", "data": message_data})
