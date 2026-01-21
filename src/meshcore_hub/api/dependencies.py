"""FastAPI dependencies for the API."""

import logging
import uuid
from threading import Lock
from typing import Annotated, Generator

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from meshcore_hub.common.database import DatabaseManager
from meshcore_hub.common.mqtt import MQTTClient, MQTTConfig

logger = logging.getLogger(__name__)

_mqtt_lock = Lock()


def get_db_manager(request: Request) -> DatabaseManager:
    """Get database manager from app.

    Args:
        request: FastAPI request

    Returns:
        DatabaseManager instance
    """
    from meshcore_hub.api.app import get_db_manager as _get_db_manager

    return _get_db_manager()


def get_db_session(
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)],
) -> Generator[Session, None, None]:
    """Get a database session.

    Args:
        db_manager: Database manager

    Yields:
        Database session
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def _build_mqtt_config(app: FastAPI) -> MQTTConfig:
    """Construct MQTT configuration from the app state."""

    mqtt_host = getattr(app.state, "mqtt_host", "localhost")
    mqtt_port = getattr(app.state, "mqtt_port", 1883)
    mqtt_prefix = getattr(app.state, "mqtt_prefix", "meshcore")
    mqtt_tls = getattr(app.state, "mqtt_tls", False)

    unique_id = uuid.uuid4().hex[:8]
    client_id = f"meshcore-api-{unique_id}"
    app.state.mqtt_client_id = client_id

    return MQTTConfig(
        host=mqtt_host,
        port=mqtt_port,
        prefix=mqtt_prefix,
        client_id=client_id,
        tls=mqtt_tls,
    )


def _create_mqtt_client(app: FastAPI) -> MQTTClient:
    """Create, connect, and start the shared MQTT client."""

    config = _build_mqtt_config(app)
    client = MQTTClient(config)
    client.connect()
    client.start_background()
    app.state.mqtt_client = client
    logger.info("Connected shared MQTT client %s", config.client_id)
    return client


def ensure_mqtt_client(app: FastAPI) -> MQTTClient:
    """Ensure a shared MQTT client exists for the application."""

    existing_client: MQTTClient | None = getattr(app.state, "mqtt_client", None)

    if existing_client is not None:
        if not existing_client.is_connected:
            logger.warning("MQTT client disconnected; publish will retry once online")
        return existing_client

    with _mqtt_lock:
        existing_client = getattr(app.state, "mqtt_client", None)
        if existing_client is None:
            existing_client = _create_mqtt_client(app)

    return existing_client


def get_mqtt_client(request: Request) -> MQTTClient:
    """FastAPI dependency wrapper around ensure_mqtt_client."""

    return ensure_mqtt_client(request.app)


def cleanup_mqtt_client(app: FastAPI) -> None:
    """Stop and disconnect the shared MQTT client when the app shuts down."""

    client: MQTTClient | None = getattr(app.state, "mqtt_client", None)
    if client is None:
        return

    try:
        client.stop()
        client.disconnect()
        logger.info(
            "Disconnected shared MQTT client %s",
            getattr(app.state, "mqtt_client_id", "<unknown>"),
        )
    finally:
        app.state.mqtt_client = None
        app.state.mqtt_client_id = None


# Dependency types for use in routes
DbSession = Annotated[Session, Depends(get_db_session)]
MqttClient = Annotated[MQTTClient, Depends(get_mqtt_client)]
