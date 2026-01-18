"""FastAPI application for MeshCore Hub Web Dashboard."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator
from zoneinfo import ZoneInfo
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from meshcore_hub import __version__
from meshcore_hub.common.schemas import RadioConfig

logger = logging.getLogger(__name__)

# Directory paths
PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
ROMANIA_TZ = ZoneInfo("Europe/Bucharest")
UTC = ZoneInfo("UTC")


def to_local_time(value: datetime | str | None, fmt: str | None = None) -> str:
    """Convert timestamps to the Romania timezone with optional formatting."""

    if value in (None, ""):
        return "-"

    dt: datetime | None = None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return value

    if dt is None:
        return "-"

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    local_dt = dt.astimezone(ROMANIA_TZ)

    if fmt:
        return local_dt.strftime(fmt)

    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Create HTTP client for API calls
    api_url = getattr(app.state, "api_url", "http://localhost:8000")
    api_key = getattr(app.state, "api_key", None)

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    app.state.http_client = httpx.AsyncClient(
        base_url=api_url,
        headers=headers,
        timeout=30.0,
    )

    # Initialize WebSocket manager
    from meshcore_hub.web.websocket import WebSocketManager

    ws_manager = WebSocketManager()
    app.state.ws_manager = ws_manager

    # Set up MQTT subscription for message events (for real-time updates)
    mqtt_client = None
    try:
        from meshcore_hub.common.config import get_web_settings
        from meshcore_hub.common.mqtt import MQTTClient, MQTTConfig

        settings = get_web_settings()
        mqtt_config = MQTTConfig(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            prefix=settings.mqtt_prefix,
            client_id=f"meshcore-web-{uuid.uuid4().hex[:8]}",
            tls=settings.mqtt_tls,
        )
        mqtt_client = MQTTClient(mqtt_config)

        # Get the event loop for running async callbacks from MQTT thread
        loop = asyncio.get_event_loop()

        async def fetch_and_broadcast_message(
            event_type: str, public_key: str, payload: dict[str, Any]
        ) -> None:
            """Fetch full message from API and broadcast to WebSocket clients."""
            try:
                # Determine message type
                message_type = "contact" if event_type == "contact_msg_recv" else "channel"

                # Extract identifying fields from payload to find the message
                # We'll fetch the latest message matching these criteria
                params: dict[str, Any] = {"limit": 1, "message_type": message_type}

                if message_type == "contact" and "pubkey_prefix" in payload:
                    params["pubkey_prefix"] = payload["pubkey_prefix"]
                elif message_type == "channel" and "channel_idx" in payload:
                    params["channel_idx"] = payload["channel_idx"]

                if "sender_timestamp" in payload:
                    from datetime import datetime, timezone

                    try:
                        sender_ts = payload["sender_timestamp"]
                        if isinstance(sender_ts, (int, float)):
                            since = datetime.fromtimestamp(sender_ts, tz=timezone.utc)
                            params["since"] = since.isoformat()
                    except (ValueError, OSError):
                        pass

                # Fetch the message from API
                response = await app.state.http_client.get("/api/v1/messages", params=params)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    if items:
                        # Broadcast the new message to all WebSocket clients
                        await ws_manager.broadcast_new_message(items[0])
                        msg_id = items[0].get("id", "unknown")
                        logger.debug(
                            "Broadcast new %s message via WebSocket (hash=%s...)",
                            message_type,
                            msg_id[:8] if isinstance(msg_id, str) else msg_id,
                        )
            except Exception as e:
                logger.warning("Failed to fetch/broadcast new message: %s", e)

        def handle_message_event(topic: str, pattern: str, payload: dict[str, Any]) -> None:
            """Handle MQTT message event (runs in MQTT thread)."""
            # Parse topic to get event type
            parts = topic.split("/")
            if len(parts) >= 4 and parts[2] == "event":
                event_type = parts[3]
                public_key = parts[1]

                # Only handle message events
                if event_type in ("contact_msg_recv", "channel_msg_recv"):
                    # Schedule async callback in event loop
                    asyncio.run_coroutine_threadsafe(
                        fetch_and_broadcast_message(event_type, public_key, payload),
                        loop,
                    )

        # Subscribe to all message events
        message_topic = f"{mqtt_config.prefix}/+/event/contact_msg_recv"
        mqtt_client.subscribe(message_topic, handle_message_event)
        channel_topic = f"{mqtt_config.prefix}/+/event/channel_msg_recv"
        mqtt_client.subscribe(channel_topic, handle_message_event)

        # Connect and start MQTT client
        mqtt_client.connect()
        mqtt_client.start_background()
        app.state.mqtt_client = mqtt_client

        logger.info("Connected to MQTT broker for real-time message updates")
    except Exception as e:
        logger.warning(f"Failed to set up MQTT subscription for real-time updates: {e}")

    logger.info(f"Web dashboard started, API URL: {api_url}")

    yield

    # Cleanup
    if mqtt_client:
        try:
            mqtt_client.stop()
            mqtt_client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting MQTT client: {e}")

    await app.state.http_client.aclose()
    logger.info("Web dashboard stopped")


def create_app(
    api_url: str | None = None,
    api_key: str | None = None,
    admin_enabled: bool | None = None,
    network_name: str | None = None,
    network_city: str | None = None,
    network_country: str | None = None,
    network_radio_config: str | None = None,
    network_contact_email: str | None = None,
    network_contact_discord: str | None = None,
    network_contact_github: str | None = None,
    network_welcome_text: str | None = None,
) -> FastAPI:
    """Create and configure the web dashboard application.

    When called without arguments (e.g., in reload mode), settings are loaded
    from environment variables via the WebSettings class.

    Args:
        api_url: Base URL of the MeshCore Hub API
        api_key: API key for authentication
        admin_enabled: Enable admin interface at /a/
        network_name: Display name for the network
        network_city: City where the network is located
        network_country: Country where the network is located
        network_radio_config: Radio configuration description
        network_contact_email: Contact email address
        network_contact_discord: Discord invite/server info
        network_contact_github: GitHub repository URL
        network_welcome_text: Welcome text for homepage

    Returns:
        Configured FastAPI application
    """
    # Load settings from environment if not provided
    from meshcore_hub.common.config import get_web_settings

    settings = get_web_settings()

    app = FastAPI(
        title="MeshCore Hub Dashboard",
        description="Web dashboard for MeshCore network visualization",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,  # Disable docs for web app
        redoc_url=None,
    )

    # Store configuration in app state (use args if provided, else settings)
    app.state.api_url = api_url or settings.api_base_url
    app.state.api_key = api_key or settings.api_key
    app.state.admin_enabled = (
        admin_enabled if admin_enabled is not None else settings.web_admin_enabled
    )
    app.state.network_name = network_name or settings.network_name
    app.state.network_city = network_city or settings.network_city
    app.state.network_country = network_country or settings.network_country
    app.state.network_radio_config = (
        network_radio_config or settings.network_radio_config
    )
    app.state.network_contact_email = (
        network_contact_email or settings.network_contact_email
    )
    app.state.network_contact_discord = (
        network_contact_discord or settings.network_contact_discord
    )
    app.state.network_contact_github = (
        network_contact_github or settings.network_contact_github
    )
    app.state.network_welcome_text = (
        network_welcome_text or settings.network_welcome_text
    )

    # Set up templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    templates.env.filters["localtime"] = to_local_time
    app.state.templates = templates

    # Mount static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include routers
    from meshcore_hub.web.routes import web_router

    app.include_router(web_router)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        """Basic health check."""
        return {"status": "healthy", "version": __version__}

    @app.get("/health/ready", tags=["Health"])
    async def health_ready(request: Request) -> dict:
        """Readiness check including API connectivity."""
        try:
            response = await request.app.state.http_client.get("/health")
            if response.status_code == 200:
                return {"status": "ready", "api": "connected"}
            return {"status": "not_ready", "api": f"status {response.status_code}"}
        except Exception as e:
            return {"status": "not_ready", "api": str(e)}

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> HTMLResponse:
        """Handle HTTP exceptions with custom error pages."""
        if exc.status_code == 404:
            context = get_network_context(request)
            context["request"] = request
            context["detail"] = exc.detail if exc.detail != "Not Found" else None
            return templates.TemplateResponse(
                "errors/404.html", context, status_code=404
            )
        # For other errors, return a simple response
        return HTMLResponse(
            content=f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>",
            status_code=exc.status_code,
        )

    return app


def get_templates(request: Request) -> Jinja2Templates:
    """Get templates from app state."""
    templates: Jinja2Templates = request.app.state.templates
    return templates


def get_network_context(request: Request) -> dict:
    """Get network configuration context for templates."""
    # Parse radio config from comma-delimited string
    radio_config = RadioConfig.from_config_string(
        request.app.state.network_radio_config
    )

    return {
        "network_name": request.app.state.network_name,
        "network_city": request.app.state.network_city,
        "network_country": request.app.state.network_country,
        "network_radio_config": radio_config,
        "network_contact_email": request.app.state.network_contact_email,
        "network_contact_discord": request.app.state.network_contact_discord,
        "network_contact_github": request.app.state.network_contact_github,
        "network_welcome_text": request.app.state.network_welcome_text,
        "admin_enabled": request.app.state.admin_enabled,
        "version": __version__,
    }
