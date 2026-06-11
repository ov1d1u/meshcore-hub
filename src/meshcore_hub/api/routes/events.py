"""Realtime WebSocket endpoints for MeshCore events."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from meshcore_hub.api.app import get_db_manager
from meshcore_hub.api.dependencies import ensure_mqtt_client
from meshcore_hub.collector.handlers.privacy import (
    PRIVACY_NAME_MARKER,
    is_privacy_blocked_name,
)
from meshcore_hub.common.database import DatabaseManager
from meshcore_hub.common.models import Node

router = APIRouter()
logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 256


def _resolve_channel_name(payload: dict[str, Any]) -> str:
    """Resolve a channel label for websocket channel message payloads."""

    channel_name = payload.get("channel_name")
    if isinstance(channel_name, str) and channel_name.strip():
        return channel_name.strip()

    channel_idx = payload.get("channel_idx")
    if isinstance(channel_idx, int):
        if channel_idx == 0:
            return "Public"
        return f"Channel {channel_idx}"
    if isinstance(channel_idx, str):
        normalized_idx = channel_idx.strip()
        if normalized_idx.isdigit():
            parsed_idx = int(normalized_idx)
            if parsed_idx == 0:
                return "Public"
            return f"Channel {parsed_idx}"

    channel_hash = payload.get("channel_hash")
    if isinstance(channel_hash, str) and channel_hash.strip():
        return f"Channel {channel_hash.strip().upper()}"

    return "Channel"


def _normalize_websocket_payload(event_name: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize websocket payload fields for frontend realtime rendering."""

    normalized_payload = dict(payload)
    if event_name == "channel_msg_recv":
        normalized_payload["channel_name"] = _resolve_channel_name(normalized_payload)
    return normalized_payload


def _enrich_advertisement_payload(
    db_manager: DatabaseManager,
    payload: dict[str, Any],
    receiver_public_key: str | None,
) -> dict[str, Any]:
    """Add hub-side metadata (admin tags, persisted name/adv_type) to a payload.

    Why: realtime advertisement payloads from the interface RECEIVER carry at
    most a contact-known `node_name` and `adv_type`. Admin-configured tag names
    and descriptions live only in the hub DB, so the WS bridge looks them up
    before forwarding so the frontend can render the correct icon and label.
    """

    source_public_key = payload.get("public_key")
    lookup_keys = [pk for pk in (source_public_key, receiver_public_key) if pk]
    if not lookup_keys:
        return payload

    session = db_manager.get_session()
    try:
        rows = (
            session.execute(
                select(Node)
                .where(Node.public_key.in_(lookup_keys))
                .options(selectinload(Node.tags))
            )
            .scalars()
            .all()
        )
    finally:
        session.close()

    nodes_by_pk = {n.public_key: n for n in rows}
    enriched = dict(payload)

    source_node = nodes_by_pk.get(source_public_key) if source_public_key else None
    if source_node is not None:
        if not enriched.get("node_name") and source_node.name:
            enriched["node_name"] = source_node.name
        if not enriched.get("adv_type") and source_node.adv_type:
            enriched["adv_type"] = source_node.adv_type
        for tag in source_node.tags:
            if tag.key == "name" and not enriched.get("node_tag_name"):
                enriched["node_tag_name"] = tag.value
            elif tag.key == "description" and not enriched.get("node_tag_description"):
                enriched["node_tag_description"] = tag.value

    receiver_node = (
        nodes_by_pk.get(receiver_public_key) if receiver_public_key else None
    )
    if receiver_node is not None:
        if not enriched.get("receiver_name") and receiver_node.name:
            enriched["receiver_name"] = receiver_node.name
        for tag in receiver_node.tags:
            if tag.key == "name" and not enriched.get("receiver_tag_name"):
                enriched["receiver_tag_name"] = tag.value
                break
    return enriched


def _should_filter_event(event_name: str | None, payload: dict[str, Any]) -> bool:
    """Return True when an event should not be sent to websocket clients."""

    if event_name != "channel_msg_recv":
        return False

    text = payload.get("text")
    if isinstance(text, str) and PRIVACY_NAME_MARKER in text:
        return True

    sender_name = payload.get("sender_name")
    if isinstance(sender_name, str) and is_privacy_blocked_name(sender_name):
        return True

    return False


@router.websocket("/events")
async def events_websocket(websocket: WebSocket) -> None:
    """Stream MQTT events to connected WebSocket clients in real time."""

    await websocket.accept()

    mqtt_client = ensure_mqtt_client(websocket.app)  # type: ignore[arg-type]
    db_manager = get_db_manager()
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

        if _should_filter_event(event_name, payload):
            return

        normalized_payload = _normalize_websocket_payload(event_name, payload)

        event = {
            "topic": topic_name,
            "pattern": pattern,
            "public_key": public_key,
            "event_name": event_name,
            "payload": normalized_payload,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        loop.call_soon_threadsafe(_enqueue, event)

    mqtt_client.subscribe(topic, handler)
    logger.info("WebSocket client subscribed to MQTT topic %s", topic)

    try:
        while True:
            message = await queue.get()
            if message.get("event_name") == "advertisement":
                try:
                    message["payload"] = await asyncio.to_thread(
                        _enrich_advertisement_payload,
                        db_manager,
                        message["payload"],
                        message.get("public_key"),
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("Failed to enrich advertisement payload")
            await websocket.send_json(message)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        raise
    finally:
        mqtt_client.remove_handler(topic, handler)