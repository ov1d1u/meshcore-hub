"""Tests for device abstraction."""

import pytest

from meshcore_hub.interface.device import (
    DeviceConfig,
    EventType,
    MeshCoreDevice,
    create_device,
)


class TestDeviceConfig:
    """Tests for DeviceConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = DeviceConfig()

        assert config.port == "/dev/ttyUSB0"
        assert config.baud == 115200
        assert config.timeout == 1.0
        assert config.reconnect_delay == 5.0
        assert config.max_reconnect_attempts == 10

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = DeviceConfig(
            port="/dev/ttyACM0",
            baud=9600,
            timeout=2.0,
        )

        assert config.port == "/dev/ttyACM0"
        assert config.baud == 9600
        assert config.timeout == 2.0


class TestEventType:
    """Tests for EventType enumeration."""

    def test_event_types(self) -> None:
        """Test event type values."""
        assert EventType.ADVERTISEMENT.value == "advertisement"
        assert EventType.CONTACT_MSG_RECV.value == "contact_msg_recv"
        assert EventType.CHANNEL_MSG_RECV.value == "channel_msg_recv"
        assert EventType.TRACE_DATA.value == "trace_data"
        assert EventType.TELEMETRY_RESPONSE.value == "telemetry_response"


class TestCreateDevice:
    """Tests for create_device factory function."""

    def test_create_mock_device(self) -> None:
        """Test creating a mock device."""
        device = create_device(mock=True)

        assert device is not None
        assert device.public_key is not None
        assert len(device.public_key) == 64

    def test_create_real_device(self) -> None:
        """Test creating a real device."""
        device = create_device(mock=False)

        assert device is not None
        assert isinstance(device, MeshCoreDevice)
