"""Member model for network member information."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meshcore_hub.common.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from meshcore_hub.common.models.member_node import MemberNode


class Member(Base, UUIDMixin, TimestampMixin):
    """Member model for network member information.

    Stores information about network members/operators.
    Members can have multiple associated nodes (chat, repeater, etc.).

    Attributes:
        id: UUID primary key
        name: Member's display name
        callsign: Amateur radio callsign (optional)
        role: Member's role in the network (optional)
        description: Additional description (optional)
        contact: Contact information (optional)
        nodes: List of associated MemberNode records
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "members"

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

    # Relationship to member nodes
    nodes: Mapped[list["MemberNode"]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Member(id={self.id}, name={self.name}, callsign={self.callsign})>"
