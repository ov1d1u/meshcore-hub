"""Tests for mock device implementation."""

import time

from meshcore_hub.interface.device import EventType
from meshcore_hub.interface.mock_device import (
    MockDeviceConfig,
    MockMeshCoreDevice,
    MockNodeConfig,
    generate_random_public_key,
)


class TestGenerateRandomPublicKey:
    """Tests for public key generation."""

    def test_generates_64_char_hex(self) -> None:
        """Test that public key is 64 hex characters."""
        key = generate_random_public_key()

        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_generates_unique_keys(self) -> None:
        """Test that generated keys are unique."""
        keys = [generate_random_public_key() for _ in range(100)]

        assert len(set(keys)) == 100


class TestMockDeviceConfig:
    """Tests for MockDeviceConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = MockDeviceConfig()

        assert config.public_key is None
        assert config.name == "MockNode"
        assert config.enable_auto_events is True
        assert config.advertisement_interval == 30.0
        assert config.message_interval == 10.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = MockDeviceConfig(
            public_key="a" * 64,
            name="CustomNode",
            enable_auto_events=False,
        )

        assert config.public_key == "a" * 64
        assert config.name == "CustomNode"
        assert config.enable_auto_events is False


class TestMockMeshCoreDevice:
    """Tests for MockMeshCoreDevice."""

    def test_connection(self, mock_device) -> None:
        """Test device connection."""
        assert not mock_device.is_connected

        result = mock_device.connect()

        assert result is True
        assert mock_device.is_connected

    def test_public_key(self, mock_device) -> None:
        """Test public key assignment."""
        assert mock_device.public_key == "a" * 64

    def test_disconnect(self, mock_device) -> None:
        """Test device disconnection."""
        mock_device.connect()
        assert mock_device.is_connected

        mock_device.disconnect()

        assert not mock_device.is_connected

    def test_send_message(self, mock_device) -> None:
        """Test sending a message."""
        mock_device.connect()

        result = mock_device.send_message(
            destination="b" * 64,
            text="Hello!",
        )

        assert result is True

    def test_send_message_not_connected(self, mock_device) -> None:
        """Test sending message when not connected."""
        result = mock_device.send_message(
            destination="b" * 64,
            text="Hello!",
        )

        assert result is False

    def test_send_channel_message(self, mock_device) -> None:
        """Test sending a channel message."""
        mock_device.connect()

        result = mock_device.send_channel_message(
            channel_idx=4,
            text="Channel message",
        )

        assert result is True

    def test_send_advertisement(self, mock_device) -> None:
        """Test sending an advertisement."""
        mock_device.connect()

        result = mock_device.send_advertisement(flood=True)

        assert result is True

    def test_request_status(self, mock_device) -> None:
        """Test requesting status."""
        mock_device.connect()

        result = mock_device.request_status()

        assert result is True

    def test_request_telemetry(self, mock_device) -> None:
        """Test requesting telemetry."""
        mock_device.connect()

        result = mock_device.request_telemetry(target="c" * 64)

        assert result is True

    def test_event_handler_registration(self, mock_device) -> None:
        """Test event handler registration."""
        events_received = []

        def handler(event_type, payload):
            events_received.append((event_type, payload))

        mock_device.register_handler(EventType.ADVERTISEMENT, handler)
        mock_device.connect()

        # Inject an event
        mock_device.inject_event(
            EventType.ADVERTISEMENT,
            {"public_key": "d" * 64, "name": "TestNode"},
        )

        # Give time for event processing
        time.sleep(0.1)

        assert len(events_received) >= 1
        event_type, payload = events_received[-1]
        assert event_type == EventType.ADVERTISEMENT
        assert payload["name"] == "TestNode"

    def test_event_handler_unregistration(self, mock_device) -> None:
        """Test event handler unregistration."""
        events_received = []

        def handler(event_type, payload):
            events_received.append((event_type, payload))

        mock_device.register_handler(EventType.ADVERTISEMENT, handler)
        mock_device.unregister_handler(EventType.ADVERTISEMENT, handler)

        mock_device.connect()
        mock_device.inject_event(
            EventType.ADVERTISEMENT,
            {"public_key": "d" * 64, "name": "TestNode"},
        )

        time.sleep(0.1)

        # Should only have the status event from connect(), not the advertisement
        advert_events = [e for e in events_received if e[0] == EventType.ADVERTISEMENT]
        assert len(advert_events) == 0

    def test_default_nodes_created(self, device_config) -> None:
        """Test that default nodes are created when none provided."""
        device = MockMeshCoreDevice(device_config)

        assert len(device.mock_config.nodes) > 0
        assert any(n.adv_type == "chat" for n in device.mock_config.nodes)
        assert any(n.adv_type == "repeater" for n in device.mock_config.nodes)

    def test_custom_nodes(self, device_config) -> None:
        """Test custom node configuration."""
        custom_nodes = [
            MockNodeConfig(
                public_key="e" * 64,
                name="CustomAlice",
                adv_type="chat",
            ),
        ]
        config = MockDeviceConfig(nodes=custom_nodes)
        device = MockMeshCoreDevice(device_config, config)

        assert len(device.mock_config.nodes) == 1
        assert device.mock_config.nodes[0].name == "CustomAlice"
