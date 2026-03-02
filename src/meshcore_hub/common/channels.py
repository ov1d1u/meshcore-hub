"""Channel-related utilities."""

from typing import Optional


def parse_allowed_channels(value: Optional[str]) -> Optional[list[str]]:
    """Parse comma-separated channel names into a list.

    Returns None if value is empty/None (meaning allow all channels).
    """
    if not value or not value.strip():
        return None
    channels = [s.strip() for s in value.split(",") if s.strip()]
    return channels if channels else None
