"""Blacklist model for ignoring nodes."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from meshcore_hub.common.models.base import Base, UUIDMixin


class Blacklist(Base, UUIDMixin):
    """Blacklist model for blocked node public keys."""

    __tablename__ = "blacklist"

    public_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Blacklist(id={self.id}, public_key={self.public_key[:12]}...)>"