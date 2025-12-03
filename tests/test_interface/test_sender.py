"""Tests for sender mode implementation."""

import pytest
from unittest.mock import MagicMock, patch

from meshcore_hub.interface.device import DeviceConfig, EventType
from meshcore_hub.interface.mock_device import MockDeviceConfig, MockMeshCoreDevice
from meshcore_hub.interface.sender import Sender, create_sender


class TestSender:
    """Tests for Sender class."""

    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        client = MagicMock()
        client.topic_builder = MagicMock()
        client.topic_builder.parse_command_topic.return_value = ("abc123", "send_msg")
        client.topic_builder.all_commands_topic.return_value = "meshcore/+/command/#"
        return client

    @pytest.fixture
    def sender(self, mock_device, mock_mqtt_client):
        """Create a sender instance."""
        return Sender(mock_device, mock_mqtt_client)

    def test_start_connects_device_and_mqtt(self, sender, mock_device, mock_mqtt_client):
        """Test that start connects to device and MQTT."""
        sender.start()

        assert mock_device.is_connected
        mock_mqtt_client.connect.assert_called_once()
        mock_mqtt_client.start_background.assert_called_once()
        mock_mqtt_client.subscribe.assert_called_once()

    def test_stop_disconnects_device_and_mqtt(self, sender, mock_device, mock_mqtt_client):
        """Test that stop disconnects device and MQTT."""
        sender.start()
        sender.stop()

        assert not mock_device.is_connected
        mock_mqtt_client.stop.assert_called_once()
        mock_mqtt_client.disconnect.assert_called_once()

    def test_handle_send_msg_command(self, sender, mock_device, mock_mqtt_client):
        """Test handling send_msg command."""
        sender.start()

        # Simulate receiving a send_msg command
        sender._handle_mqtt_message(
            topic="meshcore/abc/command/send_msg",
            pattern="meshcore/+/command/#",
            payload={
                "destination": "b" * 64,
                "text": "Hello!",
            },
        )

        # Verify message was sent (device is mocked, so just check no error)
        assert mock_device.is_connected

    def test_handle_send_channel_msg_command(self, sender, mock_device, mock_mqtt_client):
        """Test handling send_channel_msg command."""
        mock_mqtt_client.topic_builder.parse_command_topic.return_value = (
            "abc123",
            "send_channel_msg",
        )
        sender.start()

        sender._handle_mqtt_message(
            topic="meshcore/abc/command/send_channel_msg",
            pattern="meshcore/+/command/#",
            payload={
                "channel_idx": 4,
                "text": "Channel broadcast",
            },
        )

        assert mock_device.is_connected

    def test_handle_send_advert_command(self, sender, mock_device, mock_mqtt_client):
        """Test handling send_advert command."""
        mock_mqtt_client.topic_builder.parse_command_topic.return_value = (
            "abc123",
            "send_advert",
        )
        sender.start()

        sender._handle_mqtt_message(
            topic="meshcore/abc/command/send_advert",
            pattern="meshcore/+/command/#",
            payload={"flood": True},
        )

        assert mock_device.is_connected


class TestCreateSender:
    """Tests for create_sender factory function."""

    def test_creates_sender_with_mock_device(self):
        """Test creating sender with mock device."""
        with patch("meshcore_hub.interface.sender.MQTTClient") as MockMQTT:
            sender = create_sender(mock=True)

            assert sender is not None
            assert sender.device is not None
            assert sender.device.public_key is not None

    def test_creates_sender_with_custom_mqtt_config(self):
        """Test creating sender with custom MQTT configuration."""
        with patch("meshcore_hub.interface.sender.MQTTClient") as MockMQTT:
            sender = create_sender(
                mock=True,
                mqtt_host="mqtt.example.com",
                mqtt_port=8883,
                mqtt_prefix="custom",
            )

            MockMQTT.assert_called_once()
            config = MockMQTT.call_args[0][0]
            assert config.host == "mqtt.example.com"
            assert config.port == 8883
            assert config.prefix == "custom"
