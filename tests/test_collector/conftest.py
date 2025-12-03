"""Fixtures for collector component tests."""

import pytest

from meshcore_hub.common.database import DatabaseManager


@pytest.fixture
def db_manager():
    """Create an in-memory database manager for testing."""
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_tables()
    yield manager
    manager.dispose()


@pytest.fixture
def db_session(db_manager):
    """Create a database session for testing."""
    session = db_manager.get_session()
    yield session
    session.close()
