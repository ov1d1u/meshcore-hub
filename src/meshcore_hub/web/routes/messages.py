"""Messages page route."""

import logging

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from meshcore_hub.web.app import get_network_context, get_templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/messages", response_class=HTMLResponse)
async def messages_list(
    request: Request,
    message_type: str | None = Query(None, description="Filter by message type"),
    search: str | None = Query(None, description="Search in message text"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
) -> HTMLResponse:
    """Render the messages list page."""
    templates = get_templates(request)
    context = get_network_context(request)
    context["request"] = request

    # Calculate offset
    offset = (page - 1) * limit

    # Build query params
    params: dict[str, int | str] = {"limit": limit, "offset": offset}
    if message_type:
        params["message_type"] = message_type

    # Fetch messages from API
    messages = []
    total = 0

    try:
        response = await request.app.state.http_client.get(
            "/api/v1/messages", params=params
        )
        if response.status_code == 200:
            data = response.json()
            messages = data.get("items", [])
            total = data.get("total", 0)
    except Exception as e:
        logger.warning("Failed to fetch messages from API: %s", e)
        context["api_error"] = str(e)

    # Calculate pagination
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    context.update(
        {
            "messages": messages,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "message_type": message_type or "",
            "search": search or "",
        }
    )

    return templates.TemplateResponse("messages.html", context)


@router.websocket("/messages/ws")
async def messages_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time message updates."""
    ws_manager = websocket.app.state.ws_manager

    await ws_manager.connect(websocket)
    try:
        # Keep connection alive - clients don't need to send messages
        while True:
            # Wait for ping/pong or any message to keep connection alive
            data = await websocket.receive_text()
            # Echo back or ignore - we only send updates from server
            logger.debug(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        await ws_manager.disconnect(websocket)
