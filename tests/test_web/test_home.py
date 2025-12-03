"""Tests for the home page route."""

import pytest
from fastapi.testclient import TestClient


class TestHomePage:
    """Tests for the home page."""

    def test_home_returns_200(self, client: TestClient) -> None:
        """Test that home page returns 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client: TestClient) -> None:
        """Test that home page returns HTML content."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_home_contains_network_name(self, client: TestClient) -> None:
        """Test that home page contains the network name."""
        response = client.get("/")
        assert "Test Network" in response.text

    def test_home_contains_network_city(self, client: TestClient) -> None:
        """Test that home page contains the network city."""
        response = client.get("/")
        assert "Test City" in response.text

    def test_home_contains_network_country(self, client: TestClient) -> None:
        """Test that home page contains the network country."""
        response = client.get("/")
        assert "Test Country" in response.text

    def test_home_contains_radio_config(self, client: TestClient) -> None:
        """Test that home page contains the radio configuration."""
        response = client.get("/")
        assert "Test Radio Config" in response.text

    def test_home_contains_contact_email(self, client: TestClient) -> None:
        """Test that home page contains the contact email."""
        response = client.get("/")
        assert "test@example.com" in response.text

    def test_home_contains_discord_link(self, client: TestClient) -> None:
        """Test that home page contains the Discord link."""
        response = client.get("/")
        assert "discord.gg/test" in response.text

    def test_home_contains_navigation(self, client: TestClient) -> None:
        """Test that home page contains navigation links."""
        response = client.get("/")
        # Check for navigation links to other pages
        assert 'href="/"' in response.text or 'href=""' in response.text
        assert 'href="/nodes"' in response.text or "/nodes" in response.text
        assert 'href="/messages"' in response.text or "/messages" in response.text
