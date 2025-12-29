from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FileServiceSettings(BaseModel):
    type: Annotated[Literal["local", "s3"], Field(default="local")]
    basedir: Annotated[str | None, Field(default=None)]


class LoggingSettings(BaseModel):
    log_level: Annotated[int, Field(default=10)]
    format: Annotated[str, Field(default="%(name)s - %(asctime)s - %(levelname)s - %(message)s")]


class ResourcesSettings(BaseModel):
    brands: Annotated[str | None, Field(default=None)]


class WebdriverSettings(BaseModel):
    chrome_binary_path: Annotated[str | None, Field(default=None)]
    chromedriver_path: Annotated[str | None, Field(default=None)]
    chrome_options: Annotated[list[str], Field(default_factory=list)]
    use_stealth: Annotated[bool, Field(default=True)]
    timeout_seconds: Annotated[int, Field(default=30)]


class DatabaseSettings(BaseModel):
    url: Annotated[str | None, Field(default=None)]
    echo: Annotated[bool, Field(default=False)]


class HttpSettings(BaseModel):
    url: Annotated[str | None, Field(default=None)]
    client_type: Annotated[Literal["requests", "httpx"], Field(default="requests")]
    headers: Annotated[dict[str, str], Field(default_factory=dict)]


class ListingScraperSettings(BaseModel):
    min_req_delay: Annotated[float, Field(default=1.0)]
    max_req_delay: Annotated[float, Field(default=4.0)]
    timeout: Annotated[float, Field(default=20.0)]
    created_gte: Annotated[Literal["-24+hours", "-7+days", "-30+days"], Field(default="-7+days")]


class VehicleScraperSettings(BaseModel):
    min_req_delay: Annotated[float, Field(default=1.0)]
    max_req_delay: Annotated[float, Field(default=4.0)]
    timeout: Annotated[float, Field(default=20.0)]
    reinit_session_every: Annotated[int, Field(default=500)]


class ScrapersSettings(BaseModel):
    listing_scraper: Annotated[ListingScraperSettings, Field()]
    vehicle_scraper: Annotated[VehicleScraperSettings, Field()]


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A custom settings source that loads configuration from a YAML file
    based on the current environment.
    """

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # Not used in this implementation as we override __call__
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        import os

        # Determine environment and project root before validation
        env_name = os.getenv("ENVIRONMENT", "local")
        project_root = os.getenv("PROJECT_ROOT", str(PROJECT_ROOT))

        # Load the YAML configuration
        config_path = Path(project_root) / f"infra/configs/{env_name}.yml"
        if not config_path.exists():
            return {}

        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: Annotated[str, Field(default="carscout-pipe")]
    app_version: Annotated[str, Field(default=version("carscout-pipe"))]
    environment: Annotated[str, Field(default="local")]
    debug: Annotated[bool, Field(default=False)]
    project_root: Annotated[str, Field(default=str(PROJECT_ROOT))]

    file_service: Annotated[FileServiceSettings, Field()]
    logging: Annotated[LoggingSettings, Field()]
    resources: Annotated[ResourcesSettings, Field()]
    webdriver: Annotated[WebdriverSettings, Field()]
    http: Annotated[HttpSettings, Field()]
    database: Annotated[DatabaseSettings, Field()]
    scrapers: Annotated[ScrapersSettings, Field()]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Returns settings combination from difference sources in the following order of priorities:
        1. Explicitly provided values (constructor arguments)
        2. Environment variables / .env
        3. YAML configuration (infra/configs/{ENVIRONMENT}.yml)

        Performs validation of the final settings.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
        )
