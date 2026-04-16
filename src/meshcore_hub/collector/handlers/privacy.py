"""Privacy-related ingestion filters for collector handlers."""

from __future__ import annotations

PRIVACY_NAME_MARKER = "🚫"


def is_privacy_blocked_name(name: str | None, marker: str = PRIVACY_NAME_MARKER) -> bool:
    """Return True when a node name indicates it should not be tracked."""

    if not name:
        return False
    return marker in name

