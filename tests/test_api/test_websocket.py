"""Tests for the WebSocket event streaming endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi.testclient import TestClient

from meshcore_hub.api.app import create_app
from meshcore_hub.common.mqtt import TopicBuilder


class FakeMQTTClient:
    def __init__(self, prefix: str = "meshcore") -> None:
        self.topic_builder = TopicBuilder(prefix)
        self.is_connected = True
        self._handlers: dict[str, list[Callable[[str, str, dict[str, Any]], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[str, str, dict[str, Any]], None], qos: int = 1) -> None:  # noqa: D401,B950
        self._handlers.setdefault(topic, []).append(handler)

    def remove_handler(self, topic: str, handler: Callable[[str, str, dict[str, Any]], None]) -> None:  # noqa: D401,B950
        handlers = self._handlers.get(topic)
        if not handlers:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return
        if not handlers:
            self._handlers.pop(topic, None)

    def emit(self, topic: str, payload: dict[str, Any]) -> None:
        for pattern, handlers in list(self._handlers.items()):
            for handler in list(handlers):
                handler(topic, pattern, payload)

    # Lifecycle no-ops for compatibility with cleanup hooks
    def stop(self) -> None:  # noqa: D401
        return

    def disconnect(self) -> None:  # noqa: D401
        return


def test_websocket_forwards_mqtt_events() -> None:
    app = create_app()
    fake_client = FakeMQTTClient(prefix=app.state.mqtt_prefix)
    app.state.mqtt_client = fake_client

    topic = fake_client.topic_builder.event_topic("abc123", "telemetry")
    payload = {"foo": "bar"}

    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/events") as websocket:
            fake_client.emit(topic, payload)
            message = websocket.receive_json()

    assert message["public_key"] == "abc123"
    assert message["event_name"] == "telemetry"
    assert message["payload"] == payload
    assert message["topic"] == topic
```}