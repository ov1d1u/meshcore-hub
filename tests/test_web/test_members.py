"""Tests for the members page route."""

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from meshcore_hub.web.routes.members import load_members


class TestMembersPage:
    """Tests for the members page."""

    def test_members_returns_200(self, client: TestClient) -> None:
        """Test that members page returns 200 status code."""
        response = client.get("/members")
        assert response.status_code == 200

    def test_members_returns_html(self, client: TestClient) -> None:
        """Test that members page returns HTML content."""
        response = client.get("/members")
        assert "text/html" in response.headers["content-type"]

    def test_members_contains_network_name(self, client: TestClient) -> None:
        """Test that members page contains the network name."""
        response = client.get("/members")
        assert "Test Network" in response.text

    def test_members_without_file_shows_empty(self, client: TestClient) -> None:
        """Test that members page with no file shows no members."""
        response = client.get("/members")
        # Should still render successfully
        assert response.status_code == 200

    def test_members_with_file_shows_members(
        self, client_with_members: TestClient
    ) -> None:
        """Test that members page with file shows member data."""
        response = client_with_members.get("/members")
        assert response.status_code == 200
        # Check for member data
        assert "Alice" in response.text
        assert "Bob" in response.text
        assert "W1ABC" in response.text
        assert "W2XYZ" in response.text
        assert "Admin" in response.text


class TestLoadMembers:
    """Tests for the load_members function."""

    def test_load_members_none_path(self) -> None:
        """Test load_members with None path returns empty list."""
        result = load_members(None)
        assert result == []

    def test_load_members_nonexistent_file(self) -> None:
        """Test load_members with nonexistent file returns empty list."""
        result = load_members("/nonexistent/path/members.json")
        assert result == []

    def test_load_members_list_format(self) -> None:
        """Test load_members with list format JSON."""
        members_data = [
            {"name": "Alice", "callsign": "W1ABC"},
            {"name": "Bob", "callsign": "W2XYZ"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(members_data, f)
            f.flush()
            path = f.name

        try:
            result = load_members(path)
            assert len(result) == 2
            assert result[0]["name"] == "Alice"
            assert result[1]["name"] == "Bob"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_members_dict_format(self) -> None:
        """Test load_members with dict format JSON (members key)."""
        members_data = {
            "members": [
                {"name": "Alice", "callsign": "W1ABC"},
                {"name": "Bob", "callsign": "W2XYZ"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(members_data, f)
            f.flush()
            path = f.name

        try:
            result = load_members(path)
            assert len(result) == 2
            assert result[0]["name"] == "Alice"
            assert result[1]["name"] == "Bob"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_members_invalid_json(self) -> None:
        """Test load_members with invalid JSON returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            f.flush()
            path = f.name

        try:
            result = load_members(path)
            assert result == []
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_members_dict_without_members_key(self) -> None:
        """Test load_members with dict but no members key returns empty list."""
        data = {"other_key": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            result = load_members(path)
            assert result == []
        finally:
            Path(path).unlink(missing_ok=True)
