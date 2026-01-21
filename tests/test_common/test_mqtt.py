"""Tests for MQTT topic parsing utilities."""

from __future__ import annotations

from unittest.mock import Mock

from meshcore_hub.common.mqtt import MQTTClient, MQTTConfig, TopicBuilder


class TestTopicBuilder:
    """Tests for MQTT topic builder parsing helpers."""

    def test_parse_event_topic_with_single_segment_prefix(self) -> None:
        """Event topics are parsed correctly with a simple prefix."""
        builder = TopicBuilder(prefix="meshcore")

        parsed = builder.parse_event_topic(
            "meshcore/ABCDEF1234567890/event/advertisement"
        )

        assert parsed == ("ABCDEF1234567890", "advertisement")

    def test_parse_event_topic_with_multi_segment_prefix(self) -> None:
        """Event topics are parsed correctly with a slash-delimited prefix."""
        builder = TopicBuilder(prefix="meshcore/BOS")

        parsed = builder.parse_event_topic(
            "meshcore/BOS/ABCDEF1234567890/event/channel_msg_recv"
        )

        assert parsed == ("ABCDEF1234567890", "channel_msg_recv")

    def test_parse_command_topic_with_multi_segment_prefix(self) -> None:
        """Command topics are parsed correctly with a slash-delimited prefix."""
        builder = TopicBuilder(prefix="meshcore/BOS")

        parsed = builder.parse_command_topic(
            "meshcore/BOS/ABCDEF123456/command/send_msg"
        )

        assert parsed == ("ABCDEF123456", "send_msg")

    def test_parse_letsmesh_upload_topic(self) -> None:
        """LetsMesh upload topics map to public key and feed type."""
        builder = TopicBuilder(prefix="meshcore/BOS")

        parsed = builder.parse_letsmesh_upload_topic(
            "meshcore/BOS/ABCDEF1234567890/status"
        )

        assert parsed == ("ABCDEF1234567890", "status")

    def test_parse_letsmesh_upload_topic_rejects_unknown_feed(self) -> None:
        """Unknown LetsMesh feed topics are rejected."""
        builder = TopicBuilder(prefix="meshcore/BOS")

        parsed = builder.parse_letsmesh_upload_topic(
            "meshcore/BOS/ABCDEF1234567890/something_else"
        )

        assert parsed is None


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
