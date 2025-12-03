"""MeshCore device wrapper for serial communication."""

import asyncio
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
    node_address: Optional[str] = None  # Override for device public key/address


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


# Map meshcore library EventType to our EventType
MESHCORE_EVENT_MAP = {
    "advertisement": EventType.ADVERTISEMENT,
    "contact_message": EventType.CONTACT_MSG_RECV,
    "channel_message": EventType.CHANNEL_MSG_RECV,
    "trace_data": EventType.TRACE_DATA,
    "telemetry_response": EventType.TELEMETRY_RESPONSE,
    "contacts": EventType.CONTACTS,
    "message_sent": EventType.SEND_CONFIRMED,
    "status_response": EventType.STATUS_RESPONSE,
    "battery_info": EventType.BATTERY,
    "path_update": EventType.PATH_UPDATED,
}


class MeshCoreDevice(BaseMeshCoreDevice):
    """Real MeshCore device implementation using meshcore library."""

    def __init__(self, config: DeviceConfig):
        """Initialize real device.

        Args:
            config: Device configuration
        """
        super().__init__(config)
        self._running = False
        self._mc = None
        self._loop = None
        self._subscriptions = []

    def connect(self) -> bool:
        """Connect to the MeshCore device."""
        try:
            from meshcore import MeshCore
            from meshcore.serial_cx import SerialConnection
        except ImportError:
            logger.error(
                "meshcore library not installed. "
                "Install with: pip install meshcore"
            )
            return False

        try:
            logger.info(f"Connecting to MeshCore device on {self.config.port}")

            # Create event loop if needed
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            # Create serial connection and MeshCore instance
            cx = SerialConnection(
                self.config.port,
                baudrate=self.config.baud,
            )
            self._mc = MeshCore(cx, auto_reconnect=True)

            # Connect asynchronously
            self._loop.run_until_complete(self._mc.connect())

            # Get device public key from self_info property
            # After connect(), the library internally processes SELF_INFO
            # and stores it in the self_info property
            if self.config.node_address:
                # Use configured override
                self._public_key = self.config.node_address
                logger.info(f"Using configured node address: {self._public_key}")
            else:
                # Get from device self_info
                self_info = self._mc.self_info
                if self_info:
                    self._public_key = self_info.get("public_key")
                    if self._public_key:
                        logger.info(f"Retrieved device public key from self_info")
                    else:
                        logger.warning(
                            "Device self_info missing public_key field. "
                            "Use --node-address to configure manually."
                        )
                else:
                    logger.warning(
                        "Could not retrieve device self_info. "
                        "Use --node-address to configure manually."
                    )

            self._connected = True
            logger.info(f"Connected to MeshCore device, public_key: {self._public_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            return False

    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for the meshcore library."""
        if not self._mc:
            return

        from meshcore import EventType as MCEventType

        # Map of meshcore event types to subscribe to
        event_map = {
            MCEventType.ADVERTISEMENT: EventType.ADVERTISEMENT,
            MCEventType.CONTACT_MSG_RECV: EventType.CONTACT_MSG_RECV,
            MCEventType.CHANNEL_MSG_RECV: EventType.CHANNEL_MSG_RECV,
            MCEventType.TRACE_DATA: EventType.TRACE_DATA,
            MCEventType.TELEMETRY_RESPONSE: EventType.TELEMETRY_RESPONSE,
            MCEventType.CONTACTS: EventType.CONTACTS,
            MCEventType.MSG_SENT: EventType.SEND_CONFIRMED,
            MCEventType.STATUS_RESPONSE: EventType.STATUS_RESPONSE,
            MCEventType.BATTERY: EventType.BATTERY,
            MCEventType.PATH_UPDATE: EventType.PATH_UPDATED,
        }

        for mc_event_type, our_event_type in event_map.items():
            async def callback(event, et=our_event_type):
                # Convert event to dict and dispatch
                payload = dict(event.attributes) if hasattr(event, 'attributes') else {}
                self._dispatch_event(et, payload)

            sub = self._mc.subscribe(mc_event_type, callback)
            self._subscriptions.append(sub)
            logger.debug(f"Subscribed to {mc_event_type.name}")

    def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._mc:
            try:
                # Unsubscribe from events
                for sub in self._subscriptions:
                    self._mc.unsubscribe(sub)
                self._subscriptions.clear()

                # Disconnect
                if self._loop:
                    self._loop.run_until_complete(self._mc.disconnect())
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

        self._connected = False
        self._mc = None
        logger.info("Disconnected from MeshCore device")

    def send_message(
        self,
        destination: str,
        text: str,
        timestamp: Optional[int] = None,
    ) -> bool:
        """Send a direct message."""
        if not self._connected or not self._mc:
            logger.error("Cannot send message: not connected")
            return False

        try:
            async def _send():
                from meshcore.commands import send_msg
                await send_msg(self._mc, destination, text)

            self._loop.run_until_complete(_send())
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
        if not self._connected or not self._mc:
            logger.error("Cannot send channel message: not connected")
            return False

        try:
            async def _send():
                from meshcore.commands import send_channel_msg
                await send_channel_msg(self._mc, channel_idx, text)

            self._loop.run_until_complete(_send())
            logger.info(f"Sent message to channel {channel_idx}")
            return True
        except Exception as e:
            logger.error(f"Failed to send channel message: {e}")
            return False

    def send_advertisement(self, flood: bool = True) -> bool:
        """Send a node advertisement."""
        if not self._connected or not self._mc:
            logger.error("Cannot send advertisement: not connected")
            return False

        try:
            async def _send():
                from meshcore.commands import send_advert
                await send_advert(self._mc, flood=flood)

            self._loop.run_until_complete(_send())
            logger.info(f"Sent advertisement (flood={flood})")
            return True
        except Exception as e:
            logger.error(f"Failed to send advertisement: {e}")
            return False

    def request_status(self, target: Optional[str] = None) -> bool:
        """Request status from a node."""
        if not self._connected or not self._mc:
            logger.error("Cannot request status: not connected")
            return False

        try:
            async def _request():
                from meshcore.commands import request_status
                await request_status(self._mc, target)

            self._loop.run_until_complete(_request())
            logger.info(f"Requested status from {target or 'self'}")
            return True
        except Exception as e:
            logger.error(f"Failed to request status: {e}")
            return False

    def request_telemetry(self, target: str) -> bool:
        """Request telemetry from a node."""
        if not self._connected or not self._mc:
            logger.error("Cannot request telemetry: not connected")
            return False

        try:
            async def _request():
                from meshcore.commands import request_telemetry
                await request_telemetry(self._mc, target)

            self._loop.run_until_complete(_request())
            logger.info(f"Requested telemetry from {target[:12]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to request telemetry: {e}")
            return False

    def run(self) -> None:
        """Run the device event loop."""
        self._running = True
        logger.info("Starting device event loop")

        # Set up event subscriptions
        self._setup_event_subscriptions()

        # Run the async event loop
        async def _run_loop():
            while self._running and self._connected:
                await asyncio.sleep(0.1)

        try:
            self._loop.run_until_complete(_run_loop())
        except Exception as e:
            logger.error(f"Error in event loop: {e}")

        logger.info("Device event loop stopped")

    def stop(self) -> None:
        """Stop the device event loop."""
        self._running = False
        if self._mc:
            self._mc.stop()
        logger.info("Stopping device event loop")


def create_device(
    port: str = "/dev/ttyUSB0",
    baud: int = 115200,
    mock: bool = False,
    node_address: Optional[str] = None,
) -> BaseMeshCoreDevice:
    """Create a MeshCore device instance.

    Args:
        port: Serial port path
        baud: Baud rate
        mock: Use mock device for testing
        node_address: Optional override for device public key/address

    Returns:
        Device instance
    """
    config = DeviceConfig(port=port, baud=baud, node_address=node_address)

    if mock:
        from meshcore_hub.interface.mock_device import MockMeshCoreDevice
        return MockMeshCoreDevice(config)

    return MeshCoreDevice(config)
