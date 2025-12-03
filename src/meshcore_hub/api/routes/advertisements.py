"""Advertisement API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from meshcore_hub.api.auth import RequireRead
from meshcore_hub.api.dependencies import DbSession
from meshcore_hub.common.models import Advertisement
from meshcore_hub.common.schemas.messages import AdvertisementList, AdvertisementRead

router = APIRouter()


@router.get("", response_model=AdvertisementList)
async def list_advertisements(
    _: RequireRead,
    session: DbSession,
    public_key: Optional[str] = Query(None, description="Filter by public key"),
    since: Optional[datetime] = Query(None, description="Start timestamp"),
    until: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> AdvertisementList:
    """List advertisements with filtering and pagination."""
    # Build query
    query = select(Advertisement)

    if public_key:
        query = query.where(Advertisement.public_key == public_key)

    if since:
        query = query.where(Advertisement.received_at >= since)

    if until:
        query = query.where(Advertisement.received_at <= until)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.order_by(Advertisement.received_at.desc()).offset(offset).limit(limit)

    # Execute
    advertisements = session.execute(query).scalars().all()

    return AdvertisementList(
        items=[AdvertisementRead.model_validate(a) for a in advertisements],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{advertisement_id}", response_model=AdvertisementRead)
async def get_advertisement(
    _: RequireRead,
    session: DbSession,
    advertisement_id: str,
) -> AdvertisementRead:
    """Get a single advertisement by ID."""
    query = select(Advertisement).where(Advertisement.id == advertisement_id)
    advertisement = session.execute(query).scalar_one_or_none()

    if not advertisement:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    return AdvertisementRead.model_validate(advertisement)
