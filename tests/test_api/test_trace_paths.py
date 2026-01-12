"""Tests for trace path API routes."""

from datetime import datetime, timedelta, timezone


class TestListTracePaths:
    """Tests for GET /trace-paths endpoint."""

    def test_list_trace_paths_empty(self, client_no_auth):
        """Test listing trace paths when database is empty."""
        response = client_no_auth.get("/api/v1/trace-paths")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_trace_paths_with_data(self, client_no_auth, sample_trace_path):
        """Test listing trace paths with data in database."""
        response = client_no_auth.get("/api/v1/trace-paths")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["path_hashes"] == sample_trace_path.path_hashes
        assert data["items"][0]["hop_count"] == sample_trace_path.hop_count


class TestGetTracePath:
    """Tests for GET /trace-paths/{id} endpoint."""

    def test_get_trace_path_success(self, client_no_auth, sample_trace_path):
        """Test getting a specific trace path."""
        response = client_no_auth.get(f"/api/v1/trace-paths/{sample_trace_path.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["path_hashes"] == sample_trace_path.path_hashes

    def test_get_trace_path_not_found(self, client_no_auth):
        """Test getting a non-existent trace path."""
        response = client_no_auth.get("/api/v1/trace-paths/nonexistent-id")
        assert response.status_code == 404


class TestListTracePathsFilters:
    """Tests for trace path list query filters."""

    def test_filter_by_received_by(
        self,
        client_no_auth,
        sample_trace_path,
        sample_trace_path_with_receiver,
        receiver_node,
    ):
        """Test filtering trace paths by receiver node."""
        response = client_no_auth.get(
            f"/api/v1/trace-paths?received_by={receiver_node.public_key}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_filter_by_since(self, client_no_auth, api_db_session):
        """Test filtering trace paths by since timestamp."""
        from meshcore_hub.common.models import TracePath

        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=7)

        # Create old trace path
        old_trace = TracePath(
            initiator_tag=11111,
            path_hashes=["old1", "old2"],
            hop_count=2,
            received_at=old_time,
        )
        api_db_session.add(old_trace)
        api_db_session.commit()

        # Filter since yesterday - should not include old trace path
        since = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        response = client_no_auth.get(f"/api/v1/trace-paths?since={since}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_filter_by_until(self, client_no_auth, api_db_session):
        """Test filtering trace paths by until timestamp."""
        from meshcore_hub.common.models import TracePath

        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=7)

        # Create old trace path
        old_trace = TracePath(
            initiator_tag=22222,
            path_hashes=["until1", "until2"],
            hop_count=2,
            received_at=old_time,
        )
        api_db_session.add(old_trace)
        api_db_session.commit()

        # Filter until 5 days ago - should include old trace path
        until = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        response = client_no_auth.get(f"/api/v1/trace-paths?until={until}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
