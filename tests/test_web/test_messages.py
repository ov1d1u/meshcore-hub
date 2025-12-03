"""Tests for the messages page route."""

import pytest
from fastapi.testclient import TestClient

from tests.test_web.conftest import MockHttpClient


class TestMessagesPage:
    """Tests for the messages page."""

    def test_messages_returns_200(self, client: TestClient) -> None:
        """Test that messages page returns 200 status code."""
        response = client.get("/messages")
        assert response.status_code == 200

    def test_messages_returns_html(self, client: TestClient) -> None:
        """Test that messages page returns HTML content."""
        response = client.get("/messages")
        assert "text/html" in response.headers["content-type"]

    def test_messages_contains_network_name(self, client: TestClient) -> None:
        """Test that messages page contains the network name."""
        response = client.get("/messages")
        assert "Test Network" in response.text

    def test_messages_displays_message_list(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that messages page displays messages from API."""
        response = client.get("/messages")
        assert response.status_code == 200
        # Check for message data from mock
        assert "Hello World" in response.text
        assert "Channel message" in response.text

    def test_messages_displays_message_types(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that messages page displays message types."""
        response = client.get("/messages")
        # Should show message types
        assert "direct" in response.text.lower() or "contact" in response.text.lower()
        assert "channel" in response.text.lower()


class TestMessagesPageFilters:
    """Tests for messages page filtering."""

    def test_messages_with_type_filter(self, client: TestClient) -> None:
        """Test messages page with message type filter."""
        response = client.get("/messages?message_type=direct")
        assert response.status_code == 200

    def test_messages_with_channel_filter(self, client: TestClient) -> None:
        """Test messages page with channel filter."""
        response = client.get("/messages?channel_idx=0")
        assert response.status_code == 200

    def test_messages_with_search(self, client: TestClient) -> None:
        """Test messages page with search parameter."""
        response = client.get("/messages?search=hello")
        assert response.status_code == 200

    def test_messages_with_pagination(self, client: TestClient) -> None:
        """Test messages page with pagination parameters."""
        response = client.get("/messages?page=1&limit=25")
        assert response.status_code == 200

    def test_messages_page_2(self, client: TestClient) -> None:
        """Test messages page 2."""
        response = client.get("/messages?page=2")
        assert response.status_code == 200

    def test_messages_with_all_filters(self, client: TestClient) -> None:
        """Test messages page with multiple filters."""
        response = client.get(
            "/messages?message_type=channel&channel_idx=1&page=1&limit=10"
        )
        assert response.status_code == 200


class TestMessagesPageAPIErrors:
    """Tests for messages page handling API errors."""

    def test_messages_handles_api_error(
        self, web_app: any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that messages page handles API errors gracefully."""
        mock_http_client.set_response(
            "GET", "/api/v1/messages", status_code=500, json_data=None
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/messages")

        # Should still return 200 (page renders with empty list)
        assert response.status_code == 200

    def test_messages_handles_api_not_found(
        self, web_app: any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that messages page handles API 404 gracefully."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/messages",
            status_code=404,
            json_data={"detail": "Not found"},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/messages")

        # Should still return 200 (page renders with empty list)
        assert response.status_code == 200
