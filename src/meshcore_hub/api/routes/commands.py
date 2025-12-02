"""Command API routes for sending messages to the mesh network."""

import logging
import time

from fastapi import APIRouter

from meshcore_hub.api.auth import RequireAdmin
from meshcore_hub.api.dependencies import MqttClient
from meshcore_hub.common.schemas.commands import (
    CommandResponse,
    SendAdvertCommand,
    SendChannelMessageCommand,
    SendMessageCommand,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send-message", response_model=CommandResponse)
async def send_message(
    _: RequireAdmin,
    mqtt: MqttClient,
    command: SendMessageCommand,
) -> CommandResponse:
    """Send a direct message to a node.

    Publishes a send_msg command to MQTT for the sender interface to process.
    """
    try:
        # Connect to MQTT
        mqtt.connect()
        mqtt.start_background()

        # Build payload
        payload = {
            "destination": command.destination,
            "text": command.text,
            "timestamp": command.timestamp or int(time.time()),
        }

        # Publish to wildcard topic (any sender can pick it up)
        mqtt.publish_command("+", "send_msg", payload)

        # Cleanup
        mqtt.stop()
        mqtt.disconnect()

        logger.info(f"Published send_msg command to {command.destination[:12]}...")

        return CommandResponse(
            success=True,
            message=f"Message queued for {command.destination[:12]}...",
        )

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return CommandResponse(
            success=False,
            message=f"Failed to send message: {str(e)}",
        )


@router.post("/send-channel-message", response_model=CommandResponse)
async def send_channel_message(
    _: RequireAdmin,
    mqtt: MqttClient,
    command: SendChannelMessageCommand,
) -> CommandResponse:
    """Send a message to a channel.

    Publishes a send_channel_msg command to MQTT for the sender interface to process.
    """
    try:
        # Connect to MQTT
        mqtt.connect()
        mqtt.start_background()

        # Build payload
        payload = {
            "channel_idx": command.channel_idx,
            "text": command.text,
            "timestamp": command.timestamp or int(time.time()),
        }

        # Publish to wildcard topic
        mqtt.publish_command("+", "send_channel_msg", payload)

        # Cleanup
        mqtt.stop()
        mqtt.disconnect()

        logger.info(f"Published send_channel_msg command to channel {command.channel_idx}")

        return CommandResponse(
            success=True,
            message=f"Message queued for channel {command.channel_idx}",
        )

    except Exception as e:
        logger.error(f"Failed to send channel message: {e}")
        return CommandResponse(
            success=False,
            message=f"Failed to send channel message: {str(e)}",
        )


@router.post("/send-advertisement", response_model=CommandResponse)
async def send_advertisement(
    _: RequireAdmin,
    mqtt: MqttClient,
    command: SendAdvertCommand,
) -> CommandResponse:
    """Send a node advertisement.

    Publishes a send_advert command to MQTT for the sender interface to process.
    """
    try:
        # Connect to MQTT
        mqtt.connect()
        mqtt.start_background()

        # Build payload
        payload = {
            "flood": command.flood,
        }

        # Publish to wildcard topic
        mqtt.publish_command("+", "send_advert", payload)

        # Cleanup
        mqtt.stop()
        mqtt.disconnect()

        logger.info(f"Published send_advert command (flood={command.flood})")

        return CommandResponse(
            success=True,
            message=f"Advertisement queued (flood={command.flood})",
        )

    except Exception as e:
        logger.error(f"Failed to send advertisement: {e}")
        return CommandResponse(
            success=False,
            message=f"Failed to send advertisement: {str(e)}",
        )
