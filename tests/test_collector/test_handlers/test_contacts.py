"""Tests for contact handler."""

import pytest
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock

from meshcore_hub.collector.handlers.contacts import handle_contact
from meshcore_hub.common.models import Advertisement, EventReceiver, Message, Node, NodeTag


@pytest.fixture
def mock_db_manager(db_session):
    """Create a mock database manager that uses the test session."""
    mock_db = MagicMock()

    @contextmanager
    def session_scope():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    mock_db.session_scope = session_scope
    return mock_db


def test_handle_contact_creates_new_node(db_session, mock_db_manager):
    """Test that contact handler creates new node with last_seen=None."""
    payload = {
        "public_key": "a" * 64,
        "adv_name": "TestNode",
        "type": 1,  # chat
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    # Verify node was created
    node = db_session.query(Node).filter_by(public_key="a" * 64).first()
    assert node is not None
    assert node.name == "TestNode"
    assert node.adv_type == "chat"
    assert node.first_seen is not None
    assert node.last_seen is None  # Should NOT be set by contact sync


def test_handle_contact_purges_privacy_blocked_name(db_session, mock_db_manager):
    """Contact handler should purge existing data for blocked names."""
    blocked_key = "p" * 64
    receiver_key = "r" * 64
    blocked_node = Node(public_key=blocked_key, name="OldName")
    receiver_node = Node(public_key=receiver_key, name="Receiver")
    db_session.add_all([blocked_node, receiver_node])
    db_session.flush()
    db_session.add_all(
        [
            NodeTag(node_id=blocked_node.id, key="name", value="OldName"),
            Message(
                message_type="contact",
                pubkey_prefix=blocked_key[:12],
                text="Old message",
                event_hash="msg-hash-contact-1",
            ),
            Advertisement(
                public_key=blocked_key,
                name="OldName",
                event_hash="ad-hash-contact-1",
            ),
            EventReceiver(
                event_type="message",
                event_hash="msg-hash-contact-1",
                receiver_node_id=receiver_node.id,
            ),
            EventReceiver(
                event_type="advertisement",
                event_hash="ad-hash-contact-1",
                receiver_node_id=receiver_node.id,
            ),
        ]
    )
    db_session.commit()

    payload = {
        "public_key": blocked_key,
        "adv_name": "Bad🚫Node",
        "type": 1,
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    node = db_session.query(Node).filter_by(public_key=blocked_key).first()
    assert node is None
    assert (
        db_session.query(Advertisement).filter_by(public_key=blocked_key).count() == 0
    )
    assert (
        db_session.query(Message).filter_by(pubkey_prefix=blocked_key[:12]).count() == 0
    )
    assert db_session.query(NodeTag).filter_by(node_id=blocked_node.id).count() == 0
    assert (
        db_session.query(EventReceiver)
        .filter_by(event_hash="msg-hash-contact-1")
        .count()
        == 0
    )
    assert (
        db_session.query(EventReceiver)
        .filter_by(event_hash="ad-hash-contact-1")
        .count()
        == 0
    )


def test_handle_contact_updates_existing_node_name(db_session, mock_db_manager):
    """Test that contact handler updates name but NOT last_seen."""
    # Create existing node with a last_seen timestamp
    last_seen_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    node = Node(
        public_key="b" * 64,
        name="OldName",
        adv_type="chat",
        first_seen=datetime.now(timezone.utc),
        last_seen=last_seen_time,
    )
    db_session.add(node)
    db_session.commit()

    # Process contact with new name
    payload = {
        "public_key": "b" * 64,
        "adv_name": "NewName",
        "type": 1,
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    # Verify name was updated but last_seen was NOT
    db_session.expire_all()
    node = db_session.query(Node).filter_by(public_key="b" * 64).first()
    assert node.name == "NewName"
    # Compare timestamps without timezone (SQLite strips timezone info)
    assert node.last_seen is not None
    assert node.last_seen.replace(tzinfo=None) == last_seen_time.replace(tzinfo=None)


def test_handle_contact_preserves_existing_adv_type(db_session, mock_db_manager):
    """Test that contact handler doesn't overwrite existing adv_type."""
    # Create existing node with adv_type
    node = Node(
        public_key="c" * 64,
        name="TestNode",
        adv_type="repeater",
        first_seen=datetime.now(timezone.utc),
        last_seen=None,
    )
    db_session.add(node)
    db_session.commit()

    # Process contact with different type
    payload = {
        "public_key": "c" * 64,
        "adv_name": "TestNode",
        "type": 1,  # chat
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    # Verify adv_type was NOT changed
    db_session.expire_all()
    node = db_session.query(Node).filter_by(public_key="c" * 64).first()
    assert node.adv_type == "repeater"  # Should preserve existing


def test_handle_contact_sets_adv_type_if_missing(db_session, mock_db_manager):
    """Test that contact handler sets adv_type if node doesn't have one."""
    # Create existing node without adv_type
    node = Node(
        public_key="d" * 64,
        name="TestNode",
        adv_type=None,
        first_seen=datetime.now(timezone.utc),
        last_seen=None,
    )
    db_session.add(node)
    db_session.commit()

    # Process contact with type
    payload = {
        "public_key": "d" * 64,
        "adv_name": "TestNode",
        "type": 2,  # repeater
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    # Verify adv_type was set
    db_session.expire_all()
    node = db_session.query(Node).filter_by(public_key="d" * 64).first()
    assert node.adv_type == "repeater"


def test_handle_contact_ignores_missing_public_key(db_session, mock_db_manager, caplog):
    """Test that contact handler handles missing public_key gracefully."""
    payload = {
        "adv_name": "TestNode",
        "type": 1,
    }

    handle_contact("receiver123", "contact", payload, mock_db_manager)

    # Verify warning was logged and no node created
    assert "missing public_key" in caplog.text
    count = db_session.query(Node).count()
    assert count == 0


def test_handle_contact_node_type_mapping(db_session, mock_db_manager):
    """Test that numeric node types are correctly mapped to strings."""
    test_cases = [
        (0, "none"),
        (1, "chat"),
        (2, "repeater"),
        (3, "room"),
    ]

    for numeric_type, expected_string in test_cases:
        public_key = str(numeric_type) * 64
        payload = {
            "public_key": public_key,
            "adv_name": f"Node{numeric_type}",
            "type": numeric_type,
        }

        handle_contact("receiver123", "contact", payload, mock_db_manager)

        node = db_session.query(Node).filter_by(public_key=public_key).first()
        assert node.adv_type == expected_string
