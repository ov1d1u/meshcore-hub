"""Data retention and cleanup service for MeshCore Hub.

This module provides functionality to delete old event data and inactive nodes
based on configured retention policies.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from meshcore_hub.common.models import (
    Advertisement,
    EventLog,
    EventReceiver,
    Message,
    Node,
    NodeTag,
    Telemetry,
    TracePath,
)
from meshcore_hub.collector.handlers.privacy import PRIVACY_NAME_MARKER

logger = logging.getLogger(__name__)

# SQLAlchemy's `func.count()` triggers false positives in some linters.
# pylint: disable=not-callable


class CleanupStats:
    """Statistics from a cleanup operation."""

    def __init__(self) -> None:
        self.advertisements_deleted: int = 0
        self.messages_deleted: int = 0
        self.telemetry_deleted: int = 0
        self.trace_paths_deleted: int = 0
        self.event_logs_deleted: int = 0
        self.nodes_deleted: int = 0
        self.total_deleted: int = 0

    def __repr__(self) -> str:
        return (
            f"CleanupStats(total={self.total_deleted}, "
            f"advertisements={self.advertisements_deleted}, "
            f"messages={self.messages_deleted}, "
            f"telemetry={self.telemetry_deleted}, "
            f"trace_paths={self.trace_paths_deleted}, "
            f"event_logs={self.event_logs_deleted}, "
            f"nodes={self.nodes_deleted})"
        )


class PrivacyCleanupStats:
    """Statistics from a privacy cleanup operation (marker-based purge)."""

    def __init__(self) -> None:
        self.blocked_nodes: int = 0
        self.advertisements_deleted: int = 0
        self.messages_deleted: int = 0
        self.event_receivers_deleted: int = 0
        self.node_tags_deleted: int = 0
        self.nodes_deleted: int = 0
        self.total_deleted: int = 0

    def __repr__(self) -> str:
        return (
            "PrivacyCleanupStats("
            f"blocked_nodes={self.blocked_nodes}, "
            f"advertisements={self.advertisements_deleted}, "
            f"messages={self.messages_deleted}, "
            f"event_receivers={self.event_receivers_deleted}, "
            f"node_tags={self.node_tags_deleted}, "
            f"nodes={self.nodes_deleted}, "
            f"total={self.total_deleted})"
        )


async def privacy_cleanup_blocked_nodes(
    db: AsyncSession,
    marker: str = PRIVACY_NAME_MARKER,
    dry_run: bool = False,
) -> PrivacyCleanupStats:
    """Purge any already-stored data for nodes whose name contains the marker."""

    stats = PrivacyCleanupStats()

    # Find nodes whose stored name is privacy-blocked.
    blocked_nodes = (
        await db.execute(
            select(Node.id, Node.public_key).where(Node.name.isnot(None)).where(
                Node.name.contains(marker)
            )
        )
    ).all()
    stats.blocked_nodes = len(blocked_nodes)

    if not blocked_nodes:
        logger.info("Privacy cleanup: no blocked nodes found (marker=%r)", marker)
        return stats

    blocked_node_ids = [row[0] for row in blocked_nodes]
    blocked_public_keys = [row[1] for row in blocked_nodes]
    blocked_prefixes = [pk[:12] for pk in blocked_public_keys if pk]

    logger.info(
        "Privacy cleanup starting (dry_run=%s, marker=%r, nodes=%d)",
        dry_run,
        marker,
        len(blocked_node_ids),
    )

    # Collect event_hashes before deleting so we can delete junction rows too.
    msg_hashes: list[str] = []
    if blocked_prefixes:
        msg_hashes = [
            h
            for (h,) in (
                await db.execute(
                    select(Message.event_hash)
                    .where(Message.event_hash.isnot(None))
                    .where(Message.pubkey_prefix.in_(blocked_prefixes))
                )
            ).all()
            if h
        ]

    ad_hashes: list[str] = [
        h
        for (h,) in (
            await db.execute(
                select(Advertisement.event_hash)
                .where(Advertisement.event_hash.isnot(None))
                .where(Advertisement.public_key.in_(blocked_public_keys))
            )
        ).all()
        if h
    ]

    if dry_run:
        # Count rows that would be deleted.
        if blocked_prefixes:
            stats.messages_deleted = (
                await db.execute(
                    select(func.count())
                    .select_from(Message)
                    .where(Message.pubkey_prefix.in_(blocked_prefixes))
                )
            ).scalar() or 0

        stats.advertisements_deleted = (
            await db.execute(
                select(func.count())
                .select_from(Advertisement)
                .where(Advertisement.public_key.in_(blocked_public_keys))
            )
        ).scalar() or 0

        receiver_count = 0
        if msg_hashes:
            receiver_count += (
                await db.execute(
                    select(func.count())
                    .select_from(EventReceiver)
                    .where(EventReceiver.event_type == "message")
                    .where(EventReceiver.event_hash.in_(msg_hashes))
                )
            ).scalar() or 0
        if ad_hashes:
            receiver_count += (
                await db.execute(
                    select(func.count())
                    .select_from(EventReceiver)
                    .where(EventReceiver.event_type == "advertisement")
                    .where(EventReceiver.event_hash.in_(ad_hashes))
                )
            ).scalar() or 0
        stats.event_receivers_deleted = receiver_count

        stats.node_tags_deleted = (
            await db.execute(
                select(func.count())
                .select_from(NodeTag)
                .where(NodeTag.node_id.in_(blocked_node_ids))
            )
        ).scalar() or 0

        stats.nodes_deleted = (
            await db.execute(
                select(func.count()).select_from(Node).where(Node.id.in_(blocked_node_ids))
            )
        ).scalar() or 0

        stats.total_deleted = (
            stats.advertisements_deleted
            + stats.messages_deleted
            + stats.event_receivers_deleted
            + stats.node_tags_deleted
            + stats.nodes_deleted
        )

        logger.info("Privacy cleanup dry run completed: %s", stats)
        return stats

    # Live deletes.
    # Messages first (independent of node FK; keyed only by prefix).
    if blocked_prefixes:
        msg_result = await db.execute(
            delete(Message).where(Message.pubkey_prefix.in_(blocked_prefixes))
        )
        stats.messages_deleted = msg_result.rowcount or 0  # type: ignore[attr-defined]

    # Advertisements.
    ad_result = await db.execute(
        delete(Advertisement).where(Advertisement.public_key.in_(blocked_public_keys))
    )
    stats.advertisements_deleted = ad_result.rowcount or 0  # type: ignore[attr-defined]

    # Event receiver junction rows.
    receivers_deleted = 0
    if msg_hashes:
        res = await db.execute(
            delete(EventReceiver)
            .where(EventReceiver.event_type == "message")
            .where(EventReceiver.event_hash.in_(msg_hashes))
        )
        receivers_deleted += res.rowcount or 0  # type: ignore[attr-defined]
    if ad_hashes:
        res = await db.execute(
            delete(EventReceiver)
            .where(EventReceiver.event_type == "advertisement")
            .where(EventReceiver.event_hash.in_(ad_hashes))
        )
        receivers_deleted += res.rowcount or 0  # type: ignore[attr-defined]
    stats.event_receivers_deleted = receivers_deleted

    # Tags, then nodes.
    tag_res = await db.execute(delete(NodeTag).where(NodeTag.node_id.in_(blocked_node_ids)))
    stats.node_tags_deleted = tag_res.rowcount or 0  # type: ignore[attr-defined]

    node_res = await db.execute(delete(Node).where(Node.id.in_(blocked_node_ids)))
    stats.nodes_deleted = node_res.rowcount or 0  # type: ignore[attr-defined]

    await db.commit()

    stats.total_deleted = (
        stats.advertisements_deleted
        + stats.messages_deleted
        + stats.event_receivers_deleted
        + stats.node_tags_deleted
        + stats.nodes_deleted
    )
    logger.info("Privacy cleanup completed: %s", stats)
    return stats


async def cleanup_old_data(
    db: AsyncSession,
    retention_days: int,
    dry_run: bool = False,
) -> CleanupStats:
    """Delete event data older than the retention period.

    Args:
        db: Database session
        retention_days: Number of days to retain data
        dry_run: If True, only count records without deleting

    Returns:
        CleanupStats object with deletion counts
    """
    stats = CleanupStats()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info(
        "Starting data cleanup (dry_run=%s, retention_days=%d, cutoff=%s)",
        dry_run,
        retention_days,
        cutoff_date.isoformat(),
    )

    # Clean up advertisements
    stats.advertisements_deleted = await _cleanup_table(
        db, Advertisement, cutoff_date, "advertisements", dry_run
    )

    # Clean up messages
    stats.messages_deleted = await _cleanup_table(
        db, Message, cutoff_date, "messages", dry_run
    )

    # Clean up telemetry
    stats.telemetry_deleted = await _cleanup_table(
        db, Telemetry, cutoff_date, "telemetry", dry_run
    )

    # Clean up trace paths
    stats.trace_paths_deleted = await _cleanup_table(
        db, TracePath, cutoff_date, "trace_paths", dry_run
    )

    # Clean up event logs
    stats.event_logs_deleted = await _cleanup_table(
        db, EventLog, cutoff_date, "event_logs", dry_run
    )

    stats.total_deleted = (
        stats.advertisements_deleted
        + stats.messages_deleted
        + stats.telemetry_deleted
        + stats.trace_paths_deleted
        + stats.event_logs_deleted
    )

    if not dry_run:
        await db.commit()
        logger.info("Cleanup completed: %s", stats)
    else:
        logger.info("Cleanup dry run completed: %s", stats)

    return stats


async def _cleanup_table(
    db: AsyncSession,
    model: type,
    cutoff_date: datetime,
    table_name: str,
    dry_run: bool,
) -> int:
    """Delete old records from a specific table.

    Args:
        db: Database session
        model: SQLAlchemy model class
        cutoff_date: Delete records older than this date
        table_name: Name of table for logging
        dry_run: If True, only count without deleting

    Returns:
        Number of records deleted (or would be deleted in dry_run)
    """
    if dry_run:
        # Count records that would be deleted
        stmt = (
            select(func.count())
            .select_from(model)
            .where(model.created_at < cutoff_date)  # type: ignore[attr-defined]
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        logger.debug(
            "[DRY RUN] Would delete %d records from %s older than %s",
            count,
            table_name,
            cutoff_date.isoformat(),
        )
        return count
    else:
        # Delete old records
        result = await db.execute(delete(model).where(model.created_at < cutoff_date))  # type: ignore[attr-defined]
        count = result.rowcount or 0  # type: ignore[attr-defined]
        logger.debug(
            "Deleted %d records from %s older than %s",
            count,
            table_name,
            cutoff_date.isoformat(),
        )
        return count


async def cleanup_inactive_nodes(
    db: AsyncSession,
    inactivity_days: int,
    dry_run: bool = False,
) -> int:
    """Delete nodes that haven't been seen for the specified number of days.

    Only deletes nodes where last_seen is older than the cutoff date.
    Nodes with last_seen=NULL are NOT deleted (never seen on network).

    Args:
        db: Database session
        inactivity_days: Delete nodes not seen for this many days
        dry_run: If True, only count without deleting

    Returns:
        Number of nodes deleted (or would be deleted in dry_run)
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=inactivity_days)

    logger.info(
        "Starting node cleanup (dry_run=%s, inactivity_days=%d, cutoff=%s)",
        dry_run,
        inactivity_days,
        cutoff_date.isoformat(),
    )

    if dry_run:
        # Count nodes that would be deleted
        # Only count nodes with last_seen < cutoff (excludes NULL last_seen)
        stmt = (
            select(func.count())
            .select_from(Node)
            .where(Node.last_seen < cutoff_date)
            .where(Node.last_seen.isnot(None))
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        logger.info(
            "[DRY RUN] Would delete %d nodes not seen since %s",
            count,
            cutoff_date.isoformat(),
        )
        return count
    else:
        # Delete inactive nodes
        # Only delete nodes with last_seen < cutoff (excludes NULL last_seen)
        result = await db.execute(
            delete(Node)
            .where(Node.last_seen < cutoff_date)
            .where(Node.last_seen.isnot(None))
        )
        await db.commit()
        count = result.rowcount or 0  # type: ignore[attr-defined]
        logger.info(
            "Deleted %d nodes not seen since %s",
            count,
            cutoff_date.isoformat(),
        )
        return count
