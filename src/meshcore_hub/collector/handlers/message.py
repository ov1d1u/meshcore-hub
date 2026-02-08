"""Handler for message events."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from meshcore_hub.common.database import DatabaseManager
from meshcore_hub.common.hash_utils import compute_message_hash
from meshcore_hub.common.models import Blacklist, Message, Node, add_event_receiver

logger = logging.getLogger(__name__)


def handle_contact_message(
    public_key: str,
    event_type: str,
    payload: dict[str, Any],
    db: DatabaseManager,
) -> None:
    """Handle a contact message event.

    Args:
        public_key: Receiver node's public key (from MQTT topic)
        event_type: Event type name
        payload: Message payload
        db: Database manager
    """
    _handle_message(public_key, "contact", payload, db)


def handle_channel_message(
    public_key: str,
    event_type: str,
    payload: dict[str, Any],
    db: DatabaseManager,
) -> None:
    """Handle a channel message event.

    Args:
        public_key: Receiver node's public key (from MQTT topic)
        event_type: Event type name
        payload: Message payload
        db: Database manager
    """
    _handle_message(public_key, "channel", payload, db)


def _handle_message(
    public_key: str,
    message_type: str,
    payload: dict[str, Any],
    db: DatabaseManager,
) -> None:
    """Handle a message event (contact or channel).

    Args:
        public_key: Receiver node's public key
        message_type: Message type ('contact' or 'channel')
        payload: Message payload
        db: Database manager
    """
    text = payload.get("text")
    if not text:
        logger.warning("Message missing text content")
        return

    now = datetime.now(timezone.utc)

    # Extract fields based on message type
    pubkey_prefix = payload.get("pubkey_prefix") if message_type == "contact" else None
    channel_idx = payload.get("channel_idx") if message_type == "channel" else None
    path_len = payload.get("path_len")
    txt_type = payload.get("txt_type")
    signature = payload.get("signature")
    snr = payload.get("SNR") or payload.get("snr")

    # Parse sender timestamp
    sender_ts = payload.get("sender_timestamp")
    sender_timestamp = None
    if sender_ts:
        try:
            sender_timestamp = datetime.fromtimestamp(sender_ts, tz=timezone.utc)
        except (ValueError, OSError):
            pass

    # Compute event hash for deduplication
    event_hash = compute_message_hash(
        text=text,
        pubkey_prefix=pubkey_prefix,
        channel_idx=channel_idx,
        sender_timestamp=sender_timestamp,
        txt_type=txt_type,
    )

    with db.session_scope() as session:
        sender_public_key: str | None = None
        if message_type == "contact":
            sender_public_key = _resolve_sender_public_key(
                session=session,
                payload=payload,
                pubkey_prefix=pubkey_prefix,
            )

            normalized_text = text.strip().lower()
            if normalized_text in {"ignoreme", "unignoreme"}:
                if not sender_public_key:
                    logger.error(
                        "Ignore command missing sender public key (prefix=%s)",
                        pubkey_prefix,
                    )
                    return

                try:
                    if normalized_text == "ignoreme":
                        existing = session.execute(
                            select(Blacklist.id).where(
                                Blacklist.public_key == sender_public_key
                            )
                        ).scalar_one_or_none()
                        if not existing:
                            session.add(Blacklist(public_key=sender_public_key))
                            session.flush()
                    else:
                        session.execute(
                            delete(Blacklist).where(
                                Blacklist.public_key == sender_public_key
                            )
                        )
                        session.flush()
                except Exception as e:
                    logger.error("Failed to process ignore command: %s", e)
                return

            if sender_public_key:
                is_blacklisted = session.execute(
                    select(Blacklist.id).where(
                        Blacklist.public_key == sender_public_key
                    )
                ).scalar_one_or_none()
                if is_blacklisted:
                    logger.info(
                        "Skipping message from blacklisted node %s...",
                        sender_public_key[:12],
                    )
                    return
        # Find or create receiver node first (needed for both new and duplicate events)
        receiver_node = None
        if public_key:
            receiver_query = select(Node).where(Node.public_key == public_key)
            receiver_node = session.execute(receiver_query).scalar_one_or_none()

            if not receiver_node:
                receiver_node = Node(
                    public_key=public_key,
                    first_seen=now,
                    last_seen=now,
                )
                session.add(receiver_node)
                session.flush()
            else:
                receiver_node.last_seen = now

        # Check if message with same hash already exists
        existing = session.execute(
            select(Message.id).where(Message.event_hash == event_hash)
        ).scalar_one_or_none()

        if existing:
            # Event already exists - just add this receiver to the junction table
            if receiver_node:
                added = add_event_receiver(
                    session=session,
                    event_type="message",
                    event_hash=event_hash,
                    receiver_node_id=receiver_node.id,
                    snr=snr,
                    received_at=now,
                )
                if added:
                    logger.debug(
                        f"Added receiver {public_key[:12]}... to message "
                        f"(hash={event_hash[:8]}...)"
                    )
            return

        # Create message record
        message = Message(
            receiver_node_id=receiver_node.id if receiver_node else None,
            message_type=message_type,
            pubkey_prefix=pubkey_prefix,
            channel_idx=channel_idx,
            text=text,
            path_len=path_len,
            txt_type=txt_type,
            signature=signature,
            snr=snr,
            sender_timestamp=sender_timestamp,
            received_at=now,
            event_hash=event_hash,
        )
        session.add(message)

        # Add first receiver to junction table
        if receiver_node:
            add_event_receiver(
                session=session,
                event_type="message",
                event_hash=event_hash,
                receiver_node_id=receiver_node.id,
                snr=snr,
                received_at=now,
            )

        # Flush to check for duplicate constraint violation (race condition)
        try:
            session.flush()
        except IntegrityError:
            # Race condition: another request inserted the same event_hash
            session.rollback()
            logger.debug(
                f"Duplicate message skipped (race condition, hash={event_hash[:8]}...)"
            )
            # Re-add receiver to existing event in a new transaction
            if receiver_node:
                add_event_receiver(
                    session=session,
                    event_type="message",
                    event_hash=event_hash,
                    receiver_node_id=receiver_node.id,
                    snr=snr,
                    received_at=now,
                )
            return

    if message_type == "contact":
        logger.info(
            f"Stored contact message from {pubkey_prefix!r}: "
            f"{text[:30]}{'...' if len(text) > 30 else ''}"
        )
    else:
        logger.info(
            f"Stored channel {channel_idx} message: "
            f"{text[:30]}{'...' if len(text) > 30 else ''}"
        )


def _resolve_sender_public_key(
    session: Any,
    payload: dict[str, Any],
    pubkey_prefix: str | None,
) -> str | None:
    """Resolve sender public key from message payload or stored nodes.

    Args:
        session: Database session
        payload: Message payload
        pubkey_prefix: Sender's public key prefix (12 chars)

    Returns:
        Full 64-char public key if resolvable, otherwise None
    """
    payload_key = payload.get("public_key") or payload.get("sender_public_key")
    if isinstance(payload_key, str) and len(payload_key) == 64:
        return payload_key

    if not pubkey_prefix:
        return None

    matches = session.execute(
        select(Node.public_key).where(Node.public_key.like(f"{pubkey_prefix}%"))
    ).scalars().all()

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        logger.error(
            "Multiple nodes match prefix %s; cannot resolve sender public key",
            pubkey_prefix,
        )
    return None
