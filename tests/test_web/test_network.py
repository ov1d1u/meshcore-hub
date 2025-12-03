"""Tests for the network overview page route."""

import pytest
from fastapi.testclient import TestClient

from tests.test_web.conftest import MockHttpClient


class TestNetworkPage:
    """Tests for the network overview page."""

    def test_network_returns_200(self, client: TestClient) -> None:
        """Test that network page returns 200 status code."""
        response = client.get("/network")
        assert response.status_code == 200

    def test_network_returns_html(self, client: TestClient) -> None:
        """Test that network page returns HTML content."""
        response = client.get("/network")
        assert "text/html" in response.headers["content-type"]

    def test_network_contains_network_name(self, client: TestClient) -> None:
        """Test that network page contains the network name."""
        response = client.get("/network")
        assert "Test Network" in response.text

    def test_network_displays_stats(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that network page displays statistics."""
        response = client.get("/network")
        # Check for stats from mock response
        assert response.status_code == 200
        # The mock returns total_nodes: 10, active_nodes: 5, etc.
        # These should be displayed in the page
        assert "10" in response.text  # total_nodes
        assert "5" in response.text  # active_nodes

    def test_network_displays_message_counts(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that network page displays message counts."""
        response = client.get("/network")
        assert response.status_code == 200
        # Mock returns total_messages: 100, messages_today: 15
        assert "100" in response.text
        assert "15" in response.text


class TestNetworkPageAPIErrors:
    """Tests for network page handling API errors."""

    def test_network_handles_api_error(
        self, web_app: any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that network page handles API errors gracefully."""
        # Set error response for stats endpoint
        mock_http_client.set_response(
            "GET", "/api/v1/dashboard/stats", status_code=500, json_data=None
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/network")

        # Should still return 200 (page renders with defaults)
        assert response.status_code == 200

    def test_network_handles_api_not_found(
        self, web_app: any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that network page handles API 404 gracefully."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/dashboard/stats",
            status_code=404,
            json_data={"detail": "Not found"},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/network")

        # Should still return 200 (page renders with defaults)
        assert response.status_code == 200
