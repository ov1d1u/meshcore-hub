"""Member model for network member information."""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from meshcore_hub.common.models.base import Base, TimestampMixin, UUIDMixin


class Member(Base, UUIDMixin, TimestampMixin):
    """Member model for network member information.

    Stores information about network members/operators.
    Nodes are associated with members via a 'member_id' tag on the node.

    Attributes:
        id: UUID primary key
        member_id: Unique member identifier (e.g., 'walshie86')
        name: Member's display name
        callsign: Amateur radio callsign (optional)
        role: Member's role in the network (optional)
        description: Additional description (optional)
        contact: Contact information (optional)
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "members"

    member_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    callsign: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    contact: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Member(id={self.id}, member_id={self.member_id}, name={self.name}, callsign={self.callsign})>"
