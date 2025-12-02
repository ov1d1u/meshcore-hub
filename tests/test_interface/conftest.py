"""Fixtures for interface component tests."""

import pytest

from meshcore_hub.interface.device import DeviceConfig, EventType
from meshcore_hub.interface.mock_device import MockDeviceConfig, MockMeshCoreDevice


@pytest.fixture
def device_config() -> DeviceConfig:
    """Create a device configuration for testing."""
    return DeviceConfig(
        port="/dev/ttyUSB0",
        baud=115200,
        timeout=1.0,
    )


@pytest.fixture
def mock_device_config() -> MockDeviceConfig:
    """Create a mock device configuration for testing."""
    return MockDeviceConfig(
        public_key="a" * 64,
        name="TestNode",
        enable_auto_events=False,  # Disable auto events for testing
    )


@pytest.fixture
def mock_device(device_config, mock_device_config) -> MockMeshCoreDevice:
    """Create a mock device instance for testing."""
    device = MockMeshCoreDevice(device_config, mock_device_config)
    yield device
    if device.is_connected:
        device.disconnect()
