"""Members page route."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from meshcore_hub.web.app import get_network_context, get_templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/members", response_class=HTMLResponse)
async def members_page(request: Request) -> HTMLResponse:
    """Render the members page."""
    templates = get_templates(request)
    context = get_network_context(request)
    context["request"] = request

    # Fetch members from API
    members = []

    def node_sort_key(node: dict) -> int:
        """Sort nodes: repeater first, then chat, then others."""
        adv_type = (node.get("adv_type") or "").lower()
        if adv_type == "repeater":
            return 0
        if adv_type == "chat":
            return 1
        return 2

    try:
        # Fetch all members
        response = await request.app.state.http_client.get(
            "/api/v1/members", params={"limit": 100}
        )
        if response.status_code == 200:
            data = response.json()
            members = data.get("items", [])

            # Fetch all nodes with member_id tags in one query
            nodes_response = await request.app.state.http_client.get(
                "/api/v1/nodes", params={"has_tag": "member_id", "limit": 500}
            )

            # Build a map of member_id -> nodes
            member_nodes_map: dict[str, list] = {}
            if nodes_response.status_code == 200:
                nodes_data = nodes_response.json()
                all_nodes = nodes_data.get("items", [])

                for node in all_nodes:
                    # Find member_id tag
                    for tag in node.get("tags", []):
                        if tag.get("key") == "member_id":
                            member_id_value = tag.get("value")
                            if member_id_value:
                                if member_id_value not in member_nodes_map:
                                    member_nodes_map[member_id_value] = []
                                member_nodes_map[member_id_value].append(node)
                            break

            # Assign nodes to members and sort
            for member in members:
                member_id = member.get("member_id")
                if member_id and member_id in member_nodes_map:
                    # Sort nodes (repeater first, then chat, then by name tag)
                    nodes = member_nodes_map[member_id]

                    # Sort by advertisement type first, then by name
                    def full_sort_key(node: dict) -> tuple:
                        adv_type = (node.get("adv_type") or "").lower()
                        type_priority = (
                            0
                            if adv_type == "repeater"
                            else (1 if adv_type == "chat" else 2)
                        )

                        # Get name from tags
                        node_name = node.get("name") or ""
                        for tag in node.get("tags", []):
                            if tag.get("key") == "name":
                                node_name = tag.get("value") or node_name
                                break

                        return (type_priority, node_name.lower())

                    member["nodes"] = sorted(nodes, key=full_sort_key)
                else:
                    member["nodes"] = []
    except Exception as e:
        logger.warning(f"Failed to fetch members from API: {e}")
        context["api_error"] = str(e)

    context["members"] = members

    return templates.TemplateResponse("members.html", context)
