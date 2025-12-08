"""Pydantic schemas for member API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    """Schema for creating a member.

    Note: Nodes are associated with members via a 'member_id' tag on the node,
    not through this schema.
    """

    member_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique member identifier (e.g., 'walshie86')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Member's display name",
    )
    callsign: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Amateur radio callsign",
    )
    role: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Member's role in the network",
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional description",
    )
    contact: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Contact information",
    )


class MemberUpdate(BaseModel):
    """Schema for updating a member.

    Note: Nodes are associated with members via a 'member_id' tag on the node,
    not through this schema.
    """

    member_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Unique member identifier (e.g., 'walshie86')",
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Member's display name",
    )
    callsign: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Amateur radio callsign",
    )
    role: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Member's role in the network",
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional description",
    )
    contact: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Contact information",
    )


class MemberRead(BaseModel):
    """Schema for reading a member.

    Note: Nodes are associated with members via a 'member_id' tag on the node.
    To find nodes for a member, query nodes with a 'member_id' tag matching this member.
    """

    id: str = Field(..., description="Member UUID")
    member_id: str = Field(..., description="Unique member identifier")
    name: str = Field(..., description="Member's display name")
    callsign: Optional[str] = Field(default=None, description="Amateur radio callsign")
    role: Optional[str] = Field(default=None, description="Member's role")
    description: Optional[str] = Field(default=None, description="Description")
    contact: Optional[str] = Field(default=None, description="Contact information")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class MemberList(BaseModel):
    """Schema for paginated member list response."""

    items: list[MemberRead] = Field(..., description="List of members")
    total: int = Field(..., description="Total number of members")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Page offset")
