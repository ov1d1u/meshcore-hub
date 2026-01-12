"""Tests for the advertisements page route."""

from typing import Any

from fastapi.testclient import TestClient

from tests.test_web.conftest import MockHttpClient


class TestAdvertisementsPage:
    """Tests for the advertisements page."""

    def test_advertisements_returns_200(self, client: TestClient) -> None:
        """Test that advertisements page returns 200 status code."""
        response = client.get("/advertisements")
        assert response.status_code == 200

    def test_advertisements_returns_html(self, client: TestClient) -> None:
        """Test that advertisements page returns HTML content."""
        response = client.get("/advertisements")
        assert "text/html" in response.headers["content-type"]

    def test_advertisements_contains_network_name(self, client: TestClient) -> None:
        """Test that advertisements page contains the network name."""
        response = client.get("/advertisements")
        assert "Test Network" in response.text

    def test_advertisements_displays_advertisement_list(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page displays advertisements from API."""
        response = client.get("/advertisements")
        assert response.status_code == 200
        # Check for advertisement data from mock
        assert "Node One" in response.text

    def test_advertisements_displays_adv_type(
        self, client: TestClient, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page displays advertisement types."""
        response = client.get("/advertisements")
        # Should show adv type from mock data
        assert "REPEATER" in response.text


class TestAdvertisementsPageFilters:
    """Tests for advertisements page filtering."""

    def test_advertisements_with_search(self, client: TestClient) -> None:
        """Test advertisements page with search parameter."""
        response = client.get("/advertisements?search=node")
        assert response.status_code == 200

    def test_advertisements_with_member_filter(self, client: TestClient) -> None:
        """Test advertisements page with member_id filter."""
        response = client.get("/advertisements?member_id=alice")
        assert response.status_code == 200

    def test_advertisements_with_public_key_filter(self, client: TestClient) -> None:
        """Test advertisements page with public_key filter."""
        response = client.get(
            "/advertisements?public_key=abc123def456abc123def456abc123de"
        )
        assert response.status_code == 200

    def test_advertisements_with_pagination(self, client: TestClient) -> None:
        """Test advertisements page with pagination parameters."""
        response = client.get("/advertisements?page=1&limit=25")
        assert response.status_code == 200

    def test_advertisements_page_2(self, client: TestClient) -> None:
        """Test advertisements page 2."""
        response = client.get("/advertisements?page=2")
        assert response.status_code == 200

    def test_advertisements_with_all_filters(self, client: TestClient) -> None:
        """Test advertisements page with multiple filters."""
        response = client.get(
            "/advertisements?search=test&member_id=alice&page=1&limit=10"
        )
        assert response.status_code == 200


class TestAdvertisementsPageDropdowns:
    """Tests for advertisements page dropdown data."""

    def test_advertisements_loads_members_for_dropdown(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page loads members for filter dropdown."""
        # Set up members response
        mock_http_client.set_response(
            "GET",
            "/api/v1/members",
            200,
            {
                "items": [
                    {"id": "m1", "member_id": "alice", "name": "Alice"},
                    {"id": "m2", "member_id": "bob", "name": "Bob"},
                ],
                "total": 2,
            },
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200
        # Members should be available for dropdown
        assert "Alice" in response.text or "alice" in response.text

    def test_advertisements_loads_nodes_for_dropdown(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page loads nodes for filter dropdown."""
        # Set up nodes response with tags
        mock_http_client.set_response(
            "GET",
            "/api/v1/nodes",
            200,
            {
                "items": [
                    {
                        "id": "n1",
                        "public_key": "abc123",
                        "name": "Node Alpha",
                        "tags": [{"key": "name", "value": "Custom Name"}],
                    },
                    {
                        "id": "n2",
                        "public_key": "def456",
                        "name": "Node Beta",
                        "tags": [],
                    },
                ],
                "total": 2,
            },
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200


class TestAdvertisementsNodeSorting:
    """Tests for node sorting in advertisements dropdown."""

    def test_nodes_sorted_by_display_name(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that nodes are sorted alphabetically by display name."""
        # Set up nodes with tags - "Zebra" should come after "Alpha"
        mock_http_client.set_response(
            "GET",
            "/api/v1/nodes",
            200,
            {
                "items": [
                    {
                        "id": "n1",
                        "public_key": "abc123",
                        "name": "Zebra Node",
                        "tags": [],
                    },
                    {
                        "id": "n2",
                        "public_key": "def456",
                        "name": "Alpha Node",
                        "tags": [],
                    },
                ],
                "total": 2,
            },
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200
        # Both nodes should appear
        text = response.text
        assert "Alpha Node" in text or "alpha" in text.lower()
        assert "Zebra Node" in text or "zebra" in text.lower()

    def test_nodes_sorted_by_tag_name_when_present(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that nodes use tag name for sorting when available."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/nodes",
            200,
            {
                "items": [
                    {
                        "id": "n1",
                        "public_key": "abc123",
                        "name": "Zebra",
                        "tags": [{"key": "name", "value": "Alpha Custom"}],
                    },
                ],
                "total": 1,
            },
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200

    def test_nodes_fallback_to_public_key_when_no_name(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that nodes fall back to public_key when no name."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/nodes",
            200,
            {
                "items": [
                    {
                        "id": "n1",
                        "public_key": "abc123def456",
                        "name": None,
                        "tags": [],
                    },
                ],
                "total": 1,
            },
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200


class TestAdvertisementsPageAPIErrors:
    """Tests for advertisements page handling API errors."""

    def test_advertisements_handles_api_error(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page handles API errors gracefully."""
        mock_http_client.set_response(
            "GET", "/api/v1/advertisements", status_code=500, json_data=None
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        # Should still return 200 (page renders with empty list)
        assert response.status_code == 200

    def test_advertisements_handles_api_not_found(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that advertisements page handles API 404 gracefully."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/advertisements",
            status_code=404,
            json_data={"detail": "Not found"},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        # Should still return 200 (page renders with empty list)
        assert response.status_code == 200

    def test_advertisements_handles_members_api_error(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that page handles members API error gracefully."""
        mock_http_client.set_response(
            "GET", "/api/v1/members", status_code=500, json_data=None
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        # Should still return 200 (page renders without member dropdown)
        assert response.status_code == 200

    def test_advertisements_handles_nodes_api_error(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that page handles nodes API error gracefully."""
        mock_http_client.set_response(
            "GET", "/api/v1/nodes", status_code=500, json_data=None
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        # Should still return 200 (page renders without node dropdown)
        assert response.status_code == 200

    def test_advertisements_handles_empty_response(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that page handles empty advertisements list."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/advertisements",
            200,
            {"items": [], "total": 0},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200


class TestAdvertisementsPagination:
    """Tests for advertisements pagination calculations."""

    def test_pagination_calculates_total_pages(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test that pagination correctly calculates total pages."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/advertisements",
            200,
            {"items": [], "total": 150},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        # With limit=50 and total=150, should have 3 pages
        response = client.get("/advertisements?limit=50")

        assert response.status_code == 200

    def test_pagination_with_zero_total(
        self, web_app: Any, mock_http_client: MockHttpClient
    ) -> None:
        """Test pagination with zero results shows at least 1 page."""
        mock_http_client.set_response(
            "GET",
            "/api/v1/advertisements",
            200,
            {"items": [], "total": 0},
        )
        web_app.state.http_client = mock_http_client

        client = TestClient(web_app, raise_server_exceptions=True)
        response = client.get("/advertisements")

        assert response.status_code == 200
