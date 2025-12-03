"""Tests for API authentication."""


class TestAuthenticationFlow:
    """Tests for authentication behavior."""

    def test_no_auth_when_keys_not_configured(self, client_no_auth):
        """Test that no auth is required when keys are not configured."""
        # All endpoints should work without auth
        response = client_no_auth.get("/api/v1/nodes")
        assert response.status_code == 200

        response = client_no_auth.get("/api/v1/messages")
        assert response.status_code == 200

        response = client_no_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Test",
            },
        )
        assert response.status_code == 200

    def test_read_endpoints_accept_read_key(self, client_with_auth):
        """Test that read endpoints accept read key."""
        response = client_with_auth.get(
            "/api/v1/nodes",
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 200

    def test_read_endpoints_accept_admin_key(self, client_with_auth):
        """Test that read endpoints accept admin key."""
        response = client_with_auth.get(
            "/api/v1/nodes",
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 200

    def test_admin_endpoints_reject_read_key(self, client_with_auth):
        """Test that admin endpoints reject read key."""
        response = client_with_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Test",
            },
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 403

    def test_admin_endpoints_accept_admin_key(self, client_with_auth):
        """Test that admin endpoints accept admin key."""
        response = client_with_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Test",
            },
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 200

    def test_invalid_key_rejected(self, client_with_auth):
        """Test that invalid keys are rejected."""
        response = client_with_auth.get(
            "/api/v1/nodes",
            headers={"Authorization": "Bearer invalid-key"},
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix_rejected(self, client_with_auth):
        """Test that tokens without Bearer prefix are rejected."""
        response = client_with_auth.get(
            "/api/v1/nodes",
            headers={"Authorization": "test-read-key"},
        )
        assert response.status_code == 401

    def test_empty_auth_header_rejected(self, client_with_auth):
        """Test that empty auth headers are rejected."""
        response = client_with_auth.get(
            "/api/v1/nodes",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_no_auth(self, client_no_auth):
        """Test health endpoint without auth."""
        response = client_no_auth.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_with_auth_configured(self, client_with_auth):
        """Test health endpoint works even when auth is configured."""
        # Health endpoint should always be accessible
        response = client_with_auth.get("/health")
        assert response.status_code == 200
