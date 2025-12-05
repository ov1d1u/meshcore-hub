"""Member API routes."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from meshcore_hub.api.auth import RequireAdmin, RequireRead
from meshcore_hub.api.dependencies import DbSession
from meshcore_hub.common.models import Member, MemberNode
from meshcore_hub.common.schemas.members import (
    MemberCreate,
    MemberList,
    MemberRead,
    MemberUpdate,
)

router = APIRouter()


@router.get("", response_model=MemberList)
async def list_members(
    _: RequireRead,
    session: DbSession,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> MemberList:
    """List all members with pagination."""
    # Get total count
    count_query = select(func.count()).select_from(Member)
    total = session.execute(count_query).scalar() or 0

    # Get members with nodes eagerly loaded
    query = (
        select(Member)
        .options(selectinload(Member.nodes))
        .order_by(Member.name)
        .limit(limit)
        .offset(offset)
    )
    members = session.execute(query).scalars().all()

    return MemberList(
        items=[MemberRead.model_validate(m) for m in members],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{member_id}", response_model=MemberRead)
async def get_member(
    _: RequireRead,
    session: DbSession,
    member_id: str,
) -> MemberRead:
    """Get a specific member by ID."""
    query = (
        select(Member).options(selectinload(Member.nodes)).where(Member.id == member_id)
    )
    member = session.execute(query).scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    return MemberRead.model_validate(member)


@router.post("", response_model=MemberRead, status_code=201)
async def create_member(
    _: RequireAdmin,
    session: DbSession,
    member: MemberCreate,
) -> MemberRead:
    """Create a new member."""
    # Create member
    new_member = Member(
        name=member.name,
        callsign=member.callsign,
        role=member.role,
        description=member.description,
        contact=member.contact,
    )
    session.add(new_member)
    session.flush()  # Get the ID for the member

    # Add nodes if provided
    if member.nodes:
        for node_data in member.nodes:
            node = MemberNode(
                member_id=new_member.id,
                public_key=node_data.public_key.lower(),
                node_role=node_data.node_role,
            )
            session.add(node)

    session.commit()
    session.refresh(new_member)

    return MemberRead.model_validate(new_member)


@router.put("/{member_id}", response_model=MemberRead)
async def update_member(
    _: RequireAdmin,
    session: DbSession,
    member_id: str,
    member: MemberUpdate,
) -> MemberRead:
    """Update a member."""
    query = (
        select(Member).options(selectinload(Member.nodes)).where(Member.id == member_id)
    )
    existing = session.execute(query).scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="Member not found")

    # Update fields
    if member.name is not None:
        existing.name = member.name
    if member.callsign is not None:
        existing.callsign = member.callsign
    if member.role is not None:
        existing.role = member.role
    if member.description is not None:
        existing.description = member.description
    if member.contact is not None:
        existing.contact = member.contact

    # Update nodes if provided (replaces existing nodes)
    if member.nodes is not None:
        # Clear existing nodes
        existing.nodes.clear()

        # Add new nodes
        for node_data in member.nodes:
            node = MemberNode(
                member_id=existing.id,
                public_key=node_data.public_key.lower(),
                node_role=node_data.node_role,
            )
            existing.nodes.append(node)

    session.commit()
    session.refresh(existing)

    return MemberRead.model_validate(existing)


@router.delete("/{member_id}", status_code=204)
async def delete_member(
    _: RequireAdmin,
    session: DbSession,
    member_id: str,
) -> None:
    """Delete a member."""
    query = select(Member).where(Member.id == member_id)
    member = session.execute(query).scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    session.delete(member)
    session.commit()
