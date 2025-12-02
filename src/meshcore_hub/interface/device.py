"""MeshCore device wrapper for serial communication."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """MeshCore event types."""

    ADVERTISEMENT = "advertisement"
    CONTACT_MSG_RECV = "contact_msg_recv"
    CHANNEL_MSG_RECV = "channel_msg_recv"
    TRACE_DATA = "trace_data"
    TELEMETRY_RESPONSE = "telemetry_response"
    CONTACTS = "contacts"
    SEND_CONFIRMED = "send_confirmed"
    STATUS_RESPONSE = "status_response"
    BATTERY = "battery"
    PATH_UPDATED = "path_updated"


EventHandler = Callable[[EventType, dict[str, Any]], None]


@dataclass
class DeviceConfig:
    """Device connection configuration."""

    port: str = "/dev/ttyUSB0"
    baud: int = 115200
    timeout: float = 1.0
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10


class BaseMeshCoreDevice(ABC):
    """Abstract base class for MeshCore device interface."""

    def __init__(self, config: DeviceConfig):
        """Initialize device.

        Args:
            config: Device configuration
        """
        self.config = config
        self._connected = False
        self._public_key: Optional[str] = None
        self._event_handlers: dict[EventType, list[EventHandler]] = {}

    @property
    def public_key(self) -> Optional[str]:
        """Get the device's public key."""
        return self._public_key

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the device.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the device."""
        pass

    @abstractmethod
    def send_message(
        self,
        destination: str,
        text: str,
        timestamp: Optional[int] = None,
    ) -> bool:
        """Send a direct message.

        Args:
            destination: Destination public key or prefix
            text: Message content
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            True if message was queued successfully
        """
        pass

    @abstractmethod
    def send_channel_message(
        self,
        channel_idx: int,
        text: str,
        timestamp: Optional[int] = None,
    ) -> bool:
        """Send a channel message.

        Args:
            channel_idx: Channel index (0-255)
            text: Message content
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            True if message was queued successfully
        """
        pass

    @abstractmethod
    def send_advertisement(self, flood: bool = True) -> bool:
        """Send a node advertisement.

        Args:
            flood: Whether to flood the advertisement

        Returns:
            True if advertisement was queued successfully
        """
        pass

    @abstractmethod
    def request_status(self, target: Optional[str] = None) -> bool:
        """Request status from a node.

        Args:
            target: Target node public key (optional)

        Returns:
            True if request was sent
        """
        pass

    @abstractmethod
    def request_telemetry(self, target: str) -> bool:
        """Request telemetry from a node.

        Args:
            target: Target node public key

        Returns:
            True if request was sent
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """Run the device event loop (blocking)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the device event loop."""
        pass

    def register_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Register an event handler.

        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value}")

    def unregister_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Unregister an event handler.

        Args:
            event_type: Event type
            handler: Handler function to remove
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for {event_type.value}")
            except ValueError:
                pass

    def _dispatch_event(self, event_type: EventType, payload: dict[str, Any]) -> None:
        """Dispatch an event to registered handlers.

        Args:
            event_type: Event type
            payload: Event payload
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_type, payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type.value}: {e}")


class MeshCoreDevice(BaseMeshCoreDevice):
    """Real MeshCore device implementation using meshcore_py library.

    Note: This is a placeholder implementation. The actual implementation
    would use the meshcore_py library for serial communication.
    """

    def __init__(self, config: DeviceConfig):
        """Initialize real device.

        Args:
            config: Device configuration
        """
        super().__init__(config)
        self._running = False
        self._device = None

    def connect(self) -> bool:
        """Connect to the MeshCore device."""
        try:
            # Note: In actual implementation, this would use meshcore_py
            # from meshcore_py import MeshCore
            # self._device = MeshCore(self.config.port, self.config.baud)
            # self._device.connect()
            # self._public_key = self._device.get_public_key()

            logger.info(f"Connecting to MeshCore device on {self.config.port}")

            # Placeholder: In real implementation, connect via meshcore_py
            # For now, we simulate connection failure since we don't have
            # the actual device/library available
            logger.warning(
                "Real MeshCore device not available. "
                "Use --mock flag for testing."
            )
            return False

        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._device:
            try:
                # self._device.disconnect()
                pass
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        self._connected = False
        self._device = None
        logger.info("Disconnected from MeshCore device")

    def send_message(
        self,
        destination: str,
        text: str,
        timestamp: Optional[int] = None,
    ) -> bool:
        """Send a direct message."""
        if not self._connected or not self._device:
            logger.error("Cannot send message: not connected")
            return False

        try:
            ts = timestamp or int(time.time())
            # self._device.send_message(destination, text, ts)
            logger.info(f"Sent message to {destination[:12]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def send_channel_message(
        self,
        channel_idx: int,
        text: str,
        timestamp: Optional[int] = None,
    ) -> bool:
        """Send a channel message."""
        if not self._connected or not self._device:
            logger.error("Cannot send channel message: not connected")
            return False

        try:
            ts = timestamp or int(time.time())
            # self._device.send_channel_message(channel_idx, text, ts)
            logger.info(f"Sent message to channel {channel_idx}")
            return True
        except Exception as e:
            logger.error(f"Failed to send channel message: {e}")
            return False

    def send_advertisement(self, flood: bool = True) -> bool:
        """Send a node advertisement."""
        if not self._connected or not self._device:
            logger.error("Cannot send advertisement: not connected")
            return False

        try:
            # self._device.send_advertisement(flood)
            logger.info(f"Sent advertisement (flood={flood})")
            return True
        except Exception as e:
            logger.error(f"Failed to send advertisement: {e}")
            return False

    def request_status(self, target: Optional[str] = None) -> bool:
        """Request status from a node."""
        if not self._connected or not self._device:
            logger.error("Cannot request status: not connected")
            return False

        try:
            # self._device.request_status(target)
            logger.info(f"Requested status from {target or 'self'}")
            return True
        except Exception as e:
            logger.error(f"Failed to request status: {e}")
            return False

    def request_telemetry(self, target: str) -> bool:
        """Request telemetry from a node."""
        if not self._connected or not self._device:
            logger.error("Cannot request telemetry: not connected")
            return False

        try:
            # self._device.request_telemetry(target)
            logger.info(f"Requested telemetry from {target[:12]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to request telemetry: {e}")
            return False

    def run(self) -> None:
        """Run the device event loop."""
        self._running = True
        logger.info("Starting device event loop")

        while self._running and self._connected:
            try:
                # In actual implementation:
                # event = self._device.poll_event()
                # if event:
                #     event_type = EventType(event.type)
                #     self._dispatch_event(event_type, event.payload)
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in event loop: {e}")

        logger.info("Device event loop stopped")

    def stop(self) -> None:
        """Stop the device event loop."""
        self._running = False
        logger.info("Stopping device event loop")


def create_device(
    port: str = "/dev/ttyUSB0",
    baud: int = 115200,
    mock: bool = False,
) -> BaseMeshCoreDevice:
    """Create a MeshCore device instance.

    Args:
        port: Serial port path
        baud: Baud rate
        mock: Use mock device for testing

    Returns:
        Device instance
    """
    config = DeviceConfig(port=port, baud=baud)

    if mock:
        from meshcore_hub.interface.mock_device import MockMeshCoreDevice
        return MockMeshCoreDevice(config)

    return MeshCoreDevice(config)
