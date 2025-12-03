"""Tests for configuration settings."""

from meshcore_hub.common.config import (
    CommonSettings,
    InterfaceSettings,
    CollectorSettings,
    APISettings,
    WebSettings,
    LogLevel,
    InterfaceMode,
)


class TestCommonSettings:
    """Tests for CommonSettings."""

    def test_default_values(self) -> None:
        """Test default setting values without .env file influence."""
        settings = CommonSettings(_env_file=None)

        assert settings.data_home == "./data"
        assert settings.log_level == LogLevel.INFO
        assert settings.mqtt_host == "localhost"
        assert settings.mqtt_port == 1883
        assert settings.mqtt_username is None
        assert settings.mqtt_password is None
        assert settings.mqtt_prefix == "meshcore"

    def test_custom_data_home(self) -> None:
        """Test custom DATA_HOME setting."""
        settings = CommonSettings(_env_file=None, data_home="/custom/data")

        assert settings.data_home == "/custom/data"


class TestInterfaceSettings:
    """Tests for InterfaceSettings."""

    def test_default_values(self) -> None:
        """Test default setting values without .env file influence."""
        settings = InterfaceSettings(_env_file=None)

        assert settings.interface_mode == InterfaceMode.RECEIVER
        assert settings.serial_port == "/dev/ttyUSB0"
        assert settings.serial_baud == 115200
        assert settings.mock_device is False


class TestCollectorSettings:
    """Tests for CollectorSettings."""

    def test_default_values(self) -> None:
        """Test default setting values without .env file influence."""
        settings = CollectorSettings(_env_file=None)

        # database_url is None by default, effective_database_url computes it
        assert settings.database_url is None
        # Path normalizes ./data to data
        assert settings.effective_database_url == "sqlite:///data/collector/meshcore.db"
        assert settings.data_home == "./data"
        assert settings.collector_data_dir == "data/collector"
        assert settings.tags_file is None
        assert settings.effective_tags_file == "data/collector/tags.json"

    def test_custom_data_home(self) -> None:
        """Test that custom data_home affects effective paths."""
        settings = CollectorSettings(_env_file=None, data_home="/custom/data")

        assert (
            settings.effective_database_url
            == "sqlite:////custom/data/collector/meshcore.db"
        )
        assert settings.collector_data_dir == "/custom/data/collector"
        assert settings.effective_tags_file == "/custom/data/collector/tags.json"

    def test_explicit_database_url_overrides(self) -> None:
        """Test that explicit database_url overrides the default."""
        settings = CollectorSettings(
            _env_file=None, database_url="postgresql://user@host/db"
        )

        assert settings.database_url == "postgresql://user@host/db"
        assert settings.effective_database_url == "postgresql://user@host/db"


class TestAPISettings:
    """Tests for APISettings."""

    def test_default_values(self) -> None:
        """Test default setting values without .env file influence."""
        settings = APISettings(_env_file=None)

        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        # database_url is None by default, effective_database_url computes it
        assert settings.database_url is None
        # Path normalizes ./data to data
        assert settings.effective_database_url == "sqlite:///data/collector/meshcore.db"
        assert settings.api_read_key is None
        assert settings.api_admin_key is None

    def test_custom_data_home(self) -> None:
        """Test that custom data_home affects effective database path."""
        settings = APISettings(_env_file=None, data_home="/custom/data")

        assert (
            settings.effective_database_url
            == "sqlite:////custom/data/collector/meshcore.db"
        )

    def test_explicit_database_url_overrides(self) -> None:
        """Test that explicit database_url overrides the default."""
        settings = APISettings(_env_file=None, database_url="postgresql://user@host/db")

        assert settings.database_url == "postgresql://user@host/db"
        assert settings.effective_database_url == "postgresql://user@host/db"


class TestWebSettings:
    """Tests for WebSettings."""

    def test_default_values(self) -> None:
        """Test default setting values without .env file influence."""
        settings = WebSettings(_env_file=None)

        assert settings.web_host == "0.0.0.0"
        assert settings.web_port == 8080
        assert settings.api_base_url == "http://localhost:8000"
        assert settings.network_name == "MeshCore Network"
        # members_file is None by default, effective_members_file computes it
        assert settings.members_file is None
        # Path normalizes ./data to data
        assert settings.effective_members_file == "data/web/members.json"
        assert settings.web_data_dir == "data/web"

    def test_custom_data_home(self) -> None:
        """Test that custom data_home affects effective paths."""
        settings = WebSettings(_env_file=None, data_home="/custom/data")

        assert settings.effective_members_file == "/custom/data/web/members.json"
        assert settings.web_data_dir == "/custom/data/web"

    def test_explicit_members_file_overrides(self) -> None:
        """Test that explicit members_file overrides the default."""
        settings = WebSettings(_env_file=None, members_file="/path/to/members.json")

        assert settings.members_file == "/path/to/members.json"
        assert settings.effective_members_file == "/path/to/members.json"
