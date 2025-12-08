"""Import members from YAML file."""

import logging
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from sqlalchemy import select

from meshcore_hub.common.database import DatabaseManager
from meshcore_hub.common.models import Member

logger = logging.getLogger(__name__)


class MemberData(BaseModel):
    """Schema for a member entry in the import file.

    Note: Nodes are associated with members via a 'member_id' tag on the node,
    not through this schema.
    """

    member_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    callsign: Optional[str] = Field(default=None, max_length=20)
    role: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None)
    contact: Optional[str] = Field(default=None, max_length=255)


def load_members_file(file_path: str | Path) -> list[dict[str, Any]]:
    """Load and validate members from a YAML file.

    Supports two formats:
    1. List of member objects:

        - member_id: member1
          name: Member 1
          callsign: M1

    2. Object with "members" key:

        members:
          - member_id: member1
            name: Member 1
            callsign: M1

    Args:
        file_path: Path to the members YAML file

    Returns:
        List of validated member dictionaries

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If file is not valid YAML
        ValueError: If file content is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Members file not found: {file_path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # Handle both formats
    if isinstance(data, list):
        members_list = data
    elif isinstance(data, dict) and "members" in data:
        members_list = data["members"]
        if not isinstance(members_list, list):
            raise ValueError("'members' key must contain a list")
    else:
        raise ValueError("Members file must be a list or a mapping with 'members' key")

    # Validate each member
    validated: list[dict[str, Any]] = []
    for i, member in enumerate(members_list):
        if not isinstance(member, dict):
            raise ValueError(f"Member at index {i} must be an object")
        if "member_id" not in member:
            raise ValueError(f"Member at index {i} must have a 'member_id' field")
        if "name" not in member:
            raise ValueError(f"Member at index {i} must have a 'name' field")

        # Validate using Pydantic model
        try:
            validated_member = MemberData.model_validate(member)
            validated.append(validated_member.model_dump())
        except Exception as e:
            raise ValueError(f"Invalid member at index {i}: {e}")

    return validated


def import_members(
    file_path: str | Path,
    db: DatabaseManager,
) -> dict[str, Any]:
    """Import members from a YAML file into the database.

    Performs upsert operations based on member_id - existing members are updated,
    new members are created.

    Note: Nodes are associated with members via a 'member_id' tag on the node.
    This import does not manage node associations.

    Args:
        file_path: Path to the members YAML file
        db: Database manager instance

    Returns:
        Dictionary with import statistics:
        - total: Total number of members in file
        - created: Number of new members created
        - updated: Number of existing members updated
        - errors: List of error messages
    """
    stats: dict[str, Any] = {
        "total": 0,
        "created": 0,
        "updated": 0,
        "errors": [],
    }

    # Load and validate file
    try:
        members_data = load_members_file(file_path)
    except Exception as e:
        stats["errors"].append(f"Failed to load members file: {e}")
        return stats

    stats["total"] = len(members_data)

    with db.session_scope() as session:
        for member_data in members_data:
            try:
                member_id = member_data["member_id"]
                name = member_data["name"]

                # Find existing member by member_id
                query = select(Member).where(Member.member_id == member_id)
                existing = session.execute(query).scalar_one_or_none()

                if existing:
                    # Update existing member
                    if member_data.get("name") is not None:
                        existing.name = member_data["name"]
                    if member_data.get("callsign") is not None:
                        existing.callsign = member_data["callsign"]
                    if member_data.get("role") is not None:
                        existing.role = member_data["role"]
                    if member_data.get("description") is not None:
                        existing.description = member_data["description"]
                    if member_data.get("contact") is not None:
                        existing.contact = member_data["contact"]

                    stats["updated"] += 1
                    logger.debug(f"Updated member: {member_id} ({name})")
                else:
                    # Create new member
                    new_member = Member(
                        member_id=member_id,
                        name=name,
                        callsign=member_data.get("callsign"),
                        role=member_data.get("role"),
                        description=member_data.get("description"),
                        contact=member_data.get("contact"),
                    )
                    session.add(new_member)

                    stats["created"] += 1
                    logger.debug(f"Created member: {member_id} ({name})")

            except Exception as e:
                error_msg = f"Error processing member '{member_data.get('member_id', 'unknown')}' ({member_data.get('name', 'unknown')}): {e}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)

    return stats
