"""Tests for web app: config JSON escaping and trusted proxy hosts warnings."""

import json
import logging
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from meshcore_hub.web.app import _build_config_json, create_app

from .conftest import ALL_FEATURES_ENABLED, MockHttpClient


@pytest.fixture
def xss_app(mock_http_client: MockHttpClient) -> Any:
    """Create a web app with a network name containing a script injection payload."""
    app = create_app(
        api_url="http://localhost:8000",
        api_key="test-api-key",
        network_name="</script><script>alert(1)</script>",
        network_city="Test City",
        network_country="Test Country",
        network_radio_config="Test Radio Config",
        network_contact_email="test@example.com",
        features=ALL_FEATURES_ENABLED,
    )
    app.state.http_client = mock_http_client
    return app


@pytest.fixture
def xss_client(xss_app: Any, mock_http_client: MockHttpClient) -> TestClient:
    """Create a test client whose network_name contains a script injection payload."""
    xss_app.state.http_client = mock_http_client
    return TestClient(xss_app, raise_server_exceptions=True)


class TestConfigJsonXssEscaping:
    """Tests that _build_config_json escapes </script> to prevent XSS breakout."""

    def test_script_tag_escaped_in_rendered_html(self, xss_client: TestClient) -> None:
        """Config value containing </script> is escaped to <\\/script> in the HTML."""
        response = xss_client.get("/")
        assert response.status_code == 200

        html = response.text

        # The literal "</script>" must NOT appear inside the config JSON block.
        # Find the config JSON assignment to isolate the embedded block.
        config_marker = "window.__APP_CONFIG__ = "
        start = html.find(config_marker)
        assert start != -1, "Config JSON block not found in rendered HTML"
        start += len(config_marker)
        end = html.find(";", start)
        config_block = html[start:end]

        # The raw closing tag must be escaped
        assert "</script>" not in config_block
        assert "<\\/script>" in config_block

    def test_normal_config_values_unaffected(self, client: TestClient) -> None:
        """Config values without special characters render unchanged."""
        response = client.get("/")
        assert response.status_code == 200

        html = response.text
        config_marker = "window.__APP_CONFIG__ = "
        start = html.find(config_marker)
        assert start != -1
        start += len(config_marker)
        end = html.find(";", start)
        config_block = html[start:end]

        config = json.loads(config_block)
        assert config["network_name"] == "Test Network"
        assert config["network_city"] == "Test City"
        assert config["network_country"] == "Test Country"

    def test_escaped_json_is_parseable(self, xss_client: TestClient) -> None:
        """The escaped JSON is still valid and parseable by json.loads."""
        response = xss_client.get("/")
        assert response.status_code == 200

        html = response.text
        config_marker = "window.__APP_CONFIG__ = "
        start = html.find(config_marker)
        assert start != -1
        start += len(config_marker)
        end = html.find(";", start)
        config_block = html[start:end]

        # json.loads handles <\/ sequences correctly (they are valid JSON)
        config = json.loads(config_block)
        assert isinstance(config, dict)
        # The parsed value should contain the original unescaped string
        assert config["network_name"] == "</script><script>alert(1)</script>"

    def test_build_config_json_direct_escaping(self, web_app: Any) -> None:
        """Calling _build_config_json directly escapes </ sequences."""
        from starlette.requests import Request

        # Inject a malicious value into the app state
        web_app.state.network_name = "</script><script>alert(1)</script>"

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        result = _build_config_json(web_app, request)

        # Raw output must not contain literal "</script>"
        assert "</script>" not in result
        assert "<\\/script>" in result

        # Result must still be valid JSON
        parsed = json.loads(result)
        assert parsed["network_name"] == "</script><script>alert(1)</script>"

    def test_build_config_json_no_escaping_needed(self, web_app: Any) -> None:
        """_build_config_json leaves normal values intact when no </ present."""
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        result = _build_config_json(web_app, request)

        # No escaping artifacts for normal values
        assert "<\\/" not in result

        parsed = json.loads(result)
        assert parsed["network_name"] == "Test Network"
        assert parsed["network_city"] == "Test City"


class TestFlashBannerVisibility:
    """Tests for the network announcement flash banner visibility."""

    def test_banner_present_when_announcement_set(
        self, mock_http_client: MockHttpClient
    ) -> None:
        """Banner HTML is present when network_announcement is set."""
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="Scheduled maintenance at 22:00",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert 'id="flash-banner"' in html
        assert "Scheduled maintenance at 22:00" in html

    def test_banner_absent_when_announcement_none(self, client: TestClient) -> None:
        """Banner HTML is absent when network_announcement is not set."""
        response = client.get("/")
        assert response.status_code == 200
        html = response.text
        assert 'id="flash-banner"' not in html

    def test_banner_absent_for_empty_string(
        self, mock_http_client: MockHttpClient
    ) -> None:
        """Banner is not shown when announcement is an empty string."""
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        assert 'id="flash-banner"' not in response.text

    def test_banner_absent_for_whitespace_only(
        self, mock_http_client: MockHttpClient
    ) -> None:
        """Banner is not shown when announcement is whitespace-only."""
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="   ",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        assert 'id="flash-banner"' not in response.text


class TestFlashBannerMarkdown:
    """Tests for Markdown rendering in the flash banner."""

    def test_bold_rendered(self, mock_http_client: MockHttpClient) -> None:
        """Markdown bold is rendered to <strong>."""
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="**important**",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        assert "<strong>important</strong>" in response.text

    def test_link_rendered(self, mock_http_client: MockHttpClient) -> None:
        """Markdown link is rendered to <a> tag."""
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="[click here](https://example.com)",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        assert '<a href="https://example.com">click here</a>' in response.text

    def test_raw_html_passed_through(self, mock_http_client: MockHttpClient) -> None:
        """Raw HTML in announcement is passed through by the Markdown library.

        This is safe because the announcement source is an operator-controlled
        environment variable, not user input — same trust model as custom pages
        in pages.py.
        """
        app = create_app(
            api_url="http://localhost:8000",
            api_key="test-api-key",
            network_announcement="<b>bold</b>",
            features=ALL_FEATURES_ENABLED,
        )
        app.state.http_client = mock_http_client
        client = TestClient(app, raise_server_exceptions=True)

        response = client.get("/")
        assert response.status_code == 200
        assert "<b>bold</b>" in response.text


class TestTrustedProxyHostsWarning:
    """Tests for trusted proxy hosts startup warning in create_app."""

    def test_warning_logged_when_admin_enabled_and_wildcard_hosts(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A warning is logged when WEB_ADMIN_ENABLED=true and WEB_TRUSTED_PROXY_HOSTS is '*'."""
        with patch("meshcore_hub.common.config.get_web_settings") as mock_get_settings:
            from meshcore_hub.common.config import WebSettings

            settings = WebSettings(
                _env_file=None,
                web_admin_enabled=True,
                web_trusted_proxy_hosts="*",
            )
            mock_get_settings.return_value = settings

            with caplog.at_level(logging.WARNING, logger="meshcore_hub.web.app"):
                create_app(
                    api_url="http://localhost:8000",
                    admin_enabled=True,
                    features=ALL_FEATURES_ENABLED,
                )

            assert any(
                "WEB_ADMIN_ENABLED is true but WEB_TRUSTED_PROXY_HOSTS is '*'" in msg
                for msg in caplog.messages
            ), f"Expected warning not found in log messages: {caplog.messages}"

    def test_no_warning_when_trusted_proxy_hosts_is_specific(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No warning is logged when WEB_TRUSTED_PROXY_HOSTS is set to a specific value."""
        with patch("meshcore_hub.common.config.get_web_settings") as mock_get_settings:
            from meshcore_hub.common.config import WebSettings

            settings = WebSettings(
                _env_file=None,
                web_admin_enabled=True,
                web_trusted_proxy_hosts="10.0.0.1",
            )
            mock_get_settings.return_value = settings

            with caplog.at_level(logging.WARNING, logger="meshcore_hub.web.app"):
                create_app(
                    api_url="http://localhost:8000",
                    admin_enabled=True,
                    features=ALL_FEATURES_ENABLED,
                )

            assert not any(
                "WEB_TRUSTED_PROXY_HOSTS" in msg for msg in caplog.messages
            ), f"Unexpected warning found in log messages: {caplog.messages}"

    def test_no_warning_when_admin_disabled(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No warning is logged when WEB_ADMIN_ENABLED is false even with wildcard hosts."""
        with patch("meshcore_hub.common.config.get_web_settings") as mock_get_settings:
            from meshcore_hub.common.config import WebSettings

            settings = WebSettings(
                _env_file=None,
                web_admin_enabled=False,
                web_trusted_proxy_hosts="*",
            )
            mock_get_settings.return_value = settings

            with caplog.at_level(logging.WARNING, logger="meshcore_hub.web.app"):
                create_app(
                    api_url="http://localhost:8000",
                    features=ALL_FEATURES_ENABLED,
                )

            assert not any(
                "WEB_TRUSTED_PROXY_HOSTS" in msg for msg in caplog.messages
            ), f"Unexpected warning found in log messages: {caplog.messages}"

    def test_proxy_hosts_comma_list_parsed_correctly(self) -> None:
        """A comma-separated WEB_TRUSTED_PROXY_HOSTS is split into a list for middleware."""
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

        with patch("meshcore_hub.common.config.get_web_settings") as mock_get_settings:
            from meshcore_hub.common.config import WebSettings

            settings = WebSettings(
                _env_file=None,
                web_trusted_proxy_hosts="10.0.0.1, 10.0.0.2, 172.16.0.1",
            )
            mock_get_settings.return_value = settings

            app = create_app(
                api_url="http://localhost:8000",
                features=ALL_FEATURES_ENABLED,
            )

        # Find the ProxyHeadersMiddleware entry in app.user_middleware
        proxy_entries = [
            m for m in app.user_middleware if m.cls is ProxyHeadersMiddleware
        ]
        assert len(proxy_entries) == 1, "ProxyHeadersMiddleware not found in middleware"
        assert proxy_entries[0].kwargs["trusted_hosts"] == [
            "10.0.0.1",
            "10.0.0.2",
            "172.16.0.1",
        ]

    def test_wildcard_proxy_hosts_passed_as_string(self) -> None:
        """Wildcard WEB_TRUSTED_PROXY_HOSTS='*' is passed as a string to middleware."""
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

        with patch("meshcore_hub.common.config.get_web_settings") as mock_get_settings:
            from meshcore_hub.common.config import WebSettings

            settings = WebSettings(
                _env_file=None,
                web_trusted_proxy_hosts="*",
            )
            mock_get_settings.return_value = settings

            app = create_app(
                api_url="http://localhost:8000",
                features=ALL_FEATURES_ENABLED,
            )

        # Find the ProxyHeadersMiddleware entry in app.user_middleware
        proxy_entries = [
            m for m in app.user_middleware if m.cls is ProxyHeadersMiddleware
        ]
        assert len(proxy_entries) == 1, "ProxyHeadersMiddleware not found in middleware"
        assert proxy_entries[0].kwargs["trusted_hosts"] == "*"
