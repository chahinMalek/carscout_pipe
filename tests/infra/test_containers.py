from unittest.mock import patch

import pytest

from infra.containers import Container


class TestContainer:
    @pytest.fixture
    def test_config(self):
        return {
            "database": {"url": "sqlite:///:memory:", "echo": False},
            "logging": {"log_level": 10, "format_str": "%(message)s", "use_json": False},
            "webdriver": {
                "chrome_options": [],
                "use_stealth": True,
                "timeout_seconds": 30,
                "chrome_binary_path": None,
                "chromedriver_path": None,
            },
            "http": {"url": "http://test.com", "headers": {}, "client_type": "requests"},
            "file_service": {"type": "local"},
            "project_root": "/tmp",
            "resources": {"brands": "brands.json"},
            "scrapers": {
                "listing_scraper": {
                    "created_gte": "-7+days",
                    "min_req_delay": 1.0,
                    "max_req_delay": 2.0,
                    "timeout": 10.0,
                },
                "vehicle_scraper": {
                    "min_req_delay": 1.0,
                    "max_req_delay": 2.0,
                    "timeout": 10.0,
                    "reinit_session_every": 100,
                },
            },
        }

    def test_init_from_config(self, test_config):
        container = Container()
        container.config.from_dict(test_config)

        assert container.db_service() is not None
        assert container.listing_service() is not None
        assert container.vehicle_service() is not None
        assert container.run_service() is not None
        assert container.listing_scraper() is not None
        assert container.vehicle_scraper() is not None
        assert container.brand_service() is not None
        assert container.config.database.url() == "sqlite:///:memory:"

    def test_create_and_patch(self, test_config):
        env_vars = {
            "ENVIRONMENT": "test",
            "DATABASE__URL": "sqlite:///:memory:",
        }
        with (
            patch.dict("os.environ", env_vars),
            patch("infra.settings.YamlConfigSettingsSource.__call__", return_value=test_config),
        ):
            container = Container.create_and_patch()
            assert container is not None
            assert container.config.database.url() == "sqlite:///:memory:"

    def test_init_db_resource(self, in_memory_db):
        """Test that the init_db resource correctly initializes the database."""
        container = Container()
        container.db_service.override(in_memory_db)
        db_service = container.init_db()
        assert db_service == in_memory_db
