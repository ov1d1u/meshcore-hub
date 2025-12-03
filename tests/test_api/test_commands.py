"""Tests for command API routes."""


class TestSendMessage:
    """Tests for POST /commands/send-message endpoint."""

    def test_send_message_success(self, client_no_auth, mock_mqtt):
        """Test sending a direct message."""
        response = client_no_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Hello World",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "queued" in data["message"].lower()

    def test_send_message_requires_admin(self, client_with_auth):
        """Test sending message requires admin authentication."""
        # Without auth
        response = client_with_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Hello",
            },
        )
        assert response.status_code == 401

        # With read key (not admin)
        response = client_with_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Hello",
            },
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 403

        # With admin key
        response = client_with_auth.post(
            "/api/v1/commands/send-message",
            json={
                "destination": "abc123def456abc123def456abc123de",
                "text": "Hello",
            },
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 200


class TestSendChannelMessage:
    """Tests for POST /commands/send-channel-message endpoint."""

    def test_send_channel_message_success(self, client_no_auth, mock_mqtt):
        """Test sending a channel message."""
        response = client_no_auth.post(
            "/api/v1/commands/send-channel-message",
            json={
                "channel_idx": 1,
                "text": "Hello Channel",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "channel 1" in data["message"].lower()

    def test_send_channel_message_requires_admin(self, client_with_auth):
        """Test sending channel message requires admin authentication."""
        response = client_with_auth.post(
            "/api/v1/commands/send-channel-message",
            json={
                "channel_idx": 1,
                "text": "Hello",
            },
        )
        assert response.status_code == 401


class TestSendAdvertisement:
    """Tests for POST /commands/send-advertisement endpoint."""

    def test_send_advertisement_success(self, client_no_auth, mock_mqtt):
        """Test sending an advertisement."""
        response = client_no_auth.post(
            "/api/v1/commands/send-advertisement",
            json={"flood": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "advertisement" in data["message"].lower()

    def test_send_advertisement_with_flood(self, client_no_auth, mock_mqtt):
        """Test sending an advertisement with flood enabled."""
        response = client_no_auth.post(
            "/api/v1/commands/send-advertisement",
            json={"flood": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "flood=True" in data["message"]

    def test_send_advertisement_requires_admin(self, client_with_auth):
        """Test sending advertisement requires admin authentication."""
        response = client_with_auth.post(
            "/api/v1/commands/send-advertisement",
            json={"flood": False},
        )
        assert response.status_code == 401
