"""Node tag API routes."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from meshcore_hub.api.auth import RequireAdmin, RequireRead
from meshcore_hub.api.dependencies import DbSession
from meshcore_hub.common.models import Node, NodeTag
from meshcore_hub.common.schemas.nodes import (
    NodeTagCreate,
    NodeTagMove,
    NodeTagRead,
    NodeTagsCopyResult,
    NodeTagUpdate,
)

router = APIRouter()


@router.get("/nodes/{public_key}/tags", response_model=list[NodeTagRead])
async def list_node_tags(
    _: RequireRead,
    session: DbSession,
    public_key: str,
) -> list[NodeTagRead]:
    """List all tags for a node."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return [NodeTagRead.model_validate(t) for t in node.tags]


@router.get("/nodes/{public_key}/tags/{key}", response_model=NodeTagRead)
async def get_node_tag(
    _: RequireRead,
    session: DbSession,
    public_key: str,
    key: str,
) -> NodeTagRead:
    """Get a specific tag for a node."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Find tag
    tag_query = select(NodeTag).where(
        (NodeTag.node_id == node.id) & (NodeTag.key == key)
    )
    node_tag = session.execute(tag_query).scalar_one_or_none()

    if not node_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return NodeTagRead.model_validate(node_tag)


@router.post("/nodes/{public_key}/tags", response_model=NodeTagRead, status_code=201)
async def create_node_tag(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
    tag: NodeTagCreate,
) -> NodeTagRead:
    """Create a new tag for a node."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Check if tag already exists
    existing_query = select(NodeTag).where(
        (NodeTag.node_id == node.id) & (NodeTag.key == tag.key)
    )
    existing = session.execute(existing_query).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="Tag already exists")

    # Create tag
    node_tag = NodeTag(
        node_id=node.id,
        key=tag.key,
        value=tag.value,
        value_type=tag.value_type,
    )
    session.add(node_tag)
    session.commit()
    session.refresh(node_tag)

    return NodeTagRead.model_validate(node_tag)


@router.put("/nodes/{public_key}/tags/{key}", response_model=NodeTagRead)
async def update_node_tag(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
    key: str,
    tag: NodeTagUpdate,
) -> NodeTagRead:
    """Update a node tag."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Find tag
    tag_query = select(NodeTag).where(
        (NodeTag.node_id == node.id) & (NodeTag.key == key)
    )
    node_tag = session.execute(tag_query).scalar_one_or_none()

    if not node_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Update tag
    if tag.value is not None:
        node_tag.value = tag.value
    if tag.value_type is not None:
        node_tag.value_type = tag.value_type

    session.commit()
    session.refresh(node_tag)

    return NodeTagRead.model_validate(node_tag)


@router.put("/nodes/{public_key}/tags/{key}/move", response_model=NodeTagRead)
async def move_node_tag(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
    key: str,
    data: NodeTagMove,
) -> NodeTagRead:
    """Move a node tag to a different node."""
    # Check if source and destination are the same
    if public_key == data.new_public_key:
        raise HTTPException(
            status_code=400,
            detail="Source and destination nodes are the same",
        )

    # Find source node
    source_query = select(Node).where(Node.public_key == public_key)
    source_node = session.execute(source_query).scalar_one_or_none()

    if not source_node:
        raise HTTPException(status_code=404, detail="Source node not found")

    # Find tag
    tag_query = select(NodeTag).where(
        (NodeTag.node_id == source_node.id) & (NodeTag.key == key)
    )
    node_tag = session.execute(tag_query).scalar_one_or_none()

    if not node_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Find destination node
    dest_query = select(Node).where(Node.public_key == data.new_public_key)
    dest_node = session.execute(dest_query).scalar_one_or_none()

    if not dest_node:
        raise HTTPException(status_code=404, detail="Destination node not found")

    # Check if tag already exists on destination node
    conflict_query = select(NodeTag).where(
        (NodeTag.node_id == dest_node.id) & (NodeTag.key == key)
    )
    conflict = session.execute(conflict_query).scalar_one_or_none()

    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Tag '{key}' already exists on destination node",
        )

    # Move tag to destination node
    node_tag.node_id = dest_node.id
    session.commit()
    session.refresh(node_tag)

    return NodeTagRead.model_validate(node_tag)


@router.post(
    "/nodes/{public_key}/tags/copy-to/{dest_public_key}",
    response_model=NodeTagsCopyResult,
)
async def copy_all_tags(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
    dest_public_key: str,
) -> NodeTagsCopyResult:
    """Copy all tags from one node to another.

    Tags that already exist on the destination node are skipped.
    """
    # Check if source and destination are the same
    if public_key == dest_public_key:
        raise HTTPException(
            status_code=400,
            detail="Source and destination nodes are the same",
        )

    # Find source node
    source_query = select(Node).where(Node.public_key == public_key)
    source_node = session.execute(source_query).scalar_one_or_none()

    if not source_node:
        raise HTTPException(status_code=404, detail="Source node not found")

    # Find destination node
    dest_query = select(Node).where(Node.public_key == dest_public_key)
    dest_node = session.execute(dest_query).scalar_one_or_none()

    if not dest_node:
        raise HTTPException(status_code=404, detail="Destination node not found")

    # Get existing tags on destination node
    existing_query = select(NodeTag.key).where(NodeTag.node_id == dest_node.id)
    existing_keys = set(session.execute(existing_query).scalars().all())

    # Copy tags
    copied = 0
    skipped_keys = []

    for tag in source_node.tags:
        if tag.key in existing_keys:
            skipped_keys.append(tag.key)
            continue

        new_tag = NodeTag(
            node_id=dest_node.id,
            key=tag.key,
            value=tag.value,
            value_type=tag.value_type,
        )
        session.add(new_tag)
        copied += 1

    session.commit()

    return NodeTagsCopyResult(
        copied=copied,
        skipped=len(skipped_keys),
        skipped_keys=skipped_keys,
    )


@router.delete("/nodes/{public_key}/tags/{key}", status_code=204)
async def delete_node_tag(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
    key: str,
) -> None:
    """Delete a node tag."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Find and delete tag
    tag_query = select(NodeTag).where(
        (NodeTag.node_id == node.id) & (NodeTag.key == key)
    )
    node_tag = session.execute(tag_query).scalar_one_or_none()

    if not node_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    session.delete(node_tag)
    session.commit()


@router.delete("/nodes/{public_key}/tags")
async def delete_all_node_tags(
    _: RequireAdmin,
    session: DbSession,
    public_key: str,
) -> dict:
    """Delete all tags for a node."""
    # Find node
    node_query = select(Node).where(Node.public_key == public_key)
    node = session.execute(node_query).scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Count and delete all tags
    count = len(node.tags)
    for tag in node.tags:
        session.delete(tag)

    session.commit()

    return {"deleted": count}
