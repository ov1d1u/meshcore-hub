"""Realtime WebSocket endpoints for MeshCore events."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from meshcore_hub.api.dependencies import ensure_mqtt_client

router = APIRouter()
logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 256


@router.websocket("/events")
async def events_websocket(websocket: WebSocket) -> None:
    """Stream MQTT events to connected WebSocket clients in real time."""

    await websocket.accept()

    mqtt_client = ensure_mqtt_client(websocket.app)  # type: ignore[arg-type]
    topic = mqtt_client.topic_builder.all_events_topic()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_QUEUE_MAXSIZE)

    def _enqueue(event: dict[str, Any]) -> None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Dropping MQTT event because WebSocket queue is full")

    def handler(topic_name: str, pattern: str, payload: dict[str, Any]) -> None:
        public_key: str | None = None
        event_name: str | None = None
        parsed = mqtt_client.topic_builder.parse_event_topic(topic_name)
        if parsed:
            public_key, event_name = parsed

        event = {
            "topic": topic_name,
            "pattern": pattern,
            "public_key": public_key,
            "event_name": event_name,
            "payload": payload,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        loop.call_soon_threadsafe(_enqueue, event)

    mqtt_client.subscribe(topic, handler)
    logger.info("WebSocket client subscribed to MQTT topic %s", topic)

    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        raise
    finally:
        mqtt_client.remove_handler(topic, handler)