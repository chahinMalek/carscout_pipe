import os
from unittest.mock import patch

import pytest

from infra.settings import Settings, YamlConfigSettingsSource


class TestSettingsPriority:
    @pytest.fixture(autouse=True)
    def stop_dotenv(self):
        """prevents pydantic from loading the actual env file during tests"""
        model_config_mock = {
            "env_file": None,
            "case_sensitive": False,
            "env_nested_delimiter": "__",
            "extra": "ignore",
        }
        with patch.object(Settings, "model_config", model_config_mock):
            yield

    @pytest.fixture
    def mock_yaml_content(self):
        return {
            "app_name": "yaml-app",
            "logging": {
                "log_level": 20,
            },
            "database": {
                "url": "sqlite:///yaml.db",
            },
            "resources": {
                "brands": "seeds/brands.csv",
            },
            "webdriver": {
                "timeout_seconds": 30,
            },
            "http": {
                "client_type": "requests",
            },
            "file_service": {
                "type": "local",
            },
            "scrapers": {
                "listing_scraper": {"timeout": 20, "created_gte": "-7+days"},
                "vehicle_scraper": {"timeout": 20},
            },
        }

    def test_yaml_is_loaded_as_baseline(self, mock_yaml_content):
        """
        Test description:
        - Verify that values from YAML are picked up when no env vars exist.
        Expected outcome:
        - Settings are loaded from YAML file.
        """
        with patch.object(YamlConfigSettingsSource, "__call__", return_value=mock_yaml_content):
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings()
                assert settings.app_name == "yaml-app"
                assert settings.scrapers.listing_scraper.timeout == 20
                assert settings.database.url == "sqlite:///yaml.db"

    def test_env_overrides_yaml(self, mock_yaml_content):
        """
        Test description:
        - Verify that Environment Variables take precedence over YAML values.
        Expected outcome:
        - Environment variables override YAML values.
        """
        with patch.object(YamlConfigSettingsSource, "__call__", return_value=mock_yaml_content):
            env_vars = {
                "APP_NAME": "env-app",
                "SCRAPERS__LISTING_SCRAPER__TIMEOUT": "50",
                "DATABASE__URL": "sqlite:///env.db",
            }
            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings()
                assert settings.app_name == "env-app"
                assert settings.scrapers.listing_scraper.timeout == 50.0
                assert settings.database.url == "sqlite:///env.db"
                assert settings.scrapers.listing_scraper.created_gte == "-7+days"

    def test_init_overrides_all(self, mock_yaml_content):
        """
        Test description:
        - Verify that passing values to constructor (init) wins over everything.
        Expected outcome:
        - Constructor values override both YAML and environment variables.
        """
        with patch.object(YamlConfigSettingsSource, "__call__", return_value=mock_yaml_content):
            env_vars = {"APP_NAME": "env-app"}
            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings(app_name="manual-app")
                assert settings.app_name == "manual-app"

    def test_validation_still_works_on_merged_state(self, mock_yaml_content):
        """
        Test description:
        - Verify that validation is applied to the final merged result.
        Expected outcome:
        - Validation errors are raised if the final merged result is invalid.
        """
        with patch.object(YamlConfigSettingsSource, "__call__", return_value=mock_yaml_content):
            env_vars = {"SCRAPERS__LISTING_SCRAPER__CREATED_GTE": "invalid-range"}
            with patch.dict(os.environ, env_vars, clear=True):
                from pydantic import ValidationError

                with pytest.raises(ValidationError) as exc_info:
                    Settings()
                assert "created_gte" in str(exc_info.value)
                assert "Input should be" in str(exc_info.value)
