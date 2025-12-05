"""MemberNode model for associating nodes with members."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from meshcore_hub.common.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from meshcore_hub.common.models.member import Member


class MemberNode(Base, UUIDMixin, TimestampMixin):
    """Association model linking members to their nodes.

    A member can have multiple nodes (e.g., chat node, repeater).
    Each node is identified by its public_key and has a role.

    Attributes:
        id: UUID primary key
        member_id: Foreign key to the member
        public_key: Node's public key (64-char hex)
        node_role: Role of the node (e.g., 'chat', 'repeater')
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "member_nodes"

    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    public_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    node_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationship back to member
    member: Mapped["Member"] = relationship(back_populates="nodes")

    # Composite index for efficient lookups
    __table_args__ = (
        Index("ix_member_nodes_member_public_key", "member_id", "public_key"),
    )

    def __repr__(self) -> str:
        return f"<MemberNode(member_id={self.member_id}, public_key={self.public_key[:8]}..., role={self.node_role})>"
