"""Tests for meshcore_hub.common.mqtt helpers."""

from __future__ import annotations

from unittest.mock import Mock

from meshcore_hub.common.mqtt import MQTTClient, MQTTConfig


def test_remove_handler_unsubscribes_when_last_handler_removed() -> None:
    client = MQTTClient(MQTTConfig())
    client._client = Mock()  # type: ignore[attr-defined]

    def handler(topic: str, pattern: str, payload: dict[str, str]) -> None:
        return None

    topic = "meshcore/+/event/#"
    client.subscribe(topic, handler)

    client.remove_handler(topic, handler)

    assert topic not in client._message_handlers
    client._client.unsubscribe.assert_called_once_with(topic)  # type: ignore[attr-defined]


def test_remove_handler_keeps_subscription_when_handlers_remain() -> None:
    client = MQTTClient(MQTTConfig())
    client._client = Mock()  # type: ignore[attr-defined]

    def handler_one(topic: str, pattern: str, payload: dict[str, str]) -> None:
        return None

    def handler_two(topic: str, pattern: str, payload: dict[str, str]) -> None:
        return None

    topic = "meshcore/+/event/#"
    client.subscribe(topic, handler_one)
    client.subscribe(topic, handler_two)

    client.remove_handler(topic, handler_one)

    assert topic in client._message_handlers
    assert client._message_handlers[topic] == [handler_two]
    client._client.unsubscribe.assert_not_called()  # type: ignore[attr-defined]
```}