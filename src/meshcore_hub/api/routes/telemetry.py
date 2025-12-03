"""Telemetry API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from meshcore_hub.api.auth import RequireRead
from meshcore_hub.api.dependencies import DbSession
from meshcore_hub.common.models import Telemetry
from meshcore_hub.common.schemas.messages import TelemetryList, TelemetryRead

router = APIRouter()


@router.get("", response_model=TelemetryList)
async def list_telemetry(
    _: RequireRead,
    session: DbSession,
    node_public_key: Optional[str] = Query(None, description="Filter by node"),
    since: Optional[datetime] = Query(None, description="Start timestamp"),
    until: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> TelemetryList:
    """List telemetry records with filtering and pagination."""
    # Build query
    query = select(Telemetry)

    if node_public_key:
        query = query.where(Telemetry.node_public_key == node_public_key)

    if since:
        query = query.where(Telemetry.received_at >= since)

    if until:
        query = query.where(Telemetry.received_at <= until)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.order_by(Telemetry.received_at.desc()).offset(offset).limit(limit)

    # Execute
    records = session.execute(query).scalars().all()

    return TelemetryList(
        items=[TelemetryRead.model_validate(t) for t in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{telemetry_id}", response_model=TelemetryRead)
async def get_telemetry(
    _: RequireRead,
    session: DbSession,
    telemetry_id: str,
) -> TelemetryRead:
    """Get a single telemetry record by ID."""
    query = select(Telemetry).where(Telemetry.id == telemetry_id)
    telemetry = session.execute(query).scalar_one_or_none()

    if not telemetry:
        raise HTTPException(status_code=404, detail="Telemetry record not found")

    return TelemetryRead.model_validate(telemetry)
