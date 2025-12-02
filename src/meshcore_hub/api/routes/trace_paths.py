"""Trace path API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from meshcore_hub.api.auth import RequireRead
from meshcore_hub.api.dependencies import DbSession
from meshcore_hub.common.models import TracePath
from meshcore_hub.common.schemas.messages import TracePathList, TracePathRead

router = APIRouter()


@router.get("", response_model=TracePathList)
async def list_trace_paths(
    _: RequireRead,
    session: DbSession,
    since: Optional[datetime] = Query(None, description="Start timestamp"),
    until: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> TracePathList:
    """List trace paths with filtering and pagination."""
    # Build query
    query = select(TracePath)

    if since:
        query = query.where(TracePath.received_at >= since)

    if until:
        query = query.where(TracePath.received_at <= until)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.order_by(TracePath.received_at.desc()).offset(offset).limit(limit)

    # Execute
    trace_paths = session.execute(query).scalars().all()

    return TracePathList(
        items=[TracePathRead.model_validate(t) for t in trace_paths],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{trace_path_id}", response_model=TracePathRead)
async def get_trace_path(
    _: RequireRead,
    session: DbSession,
    trace_path_id: str,
) -> TracePathRead:
    """Get a single trace path by ID."""
    query = select(TracePath).where(TracePath.id == trace_path_id)
    trace_path = session.execute(query).scalar_one_or_none()

    if not trace_path:
        raise HTTPException(status_code=404, detail="Trace path not found")

    return TracePathRead.model_validate(trace_path)
