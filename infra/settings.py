from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FileServiceSettings(BaseModel):
    type: Literal["local", "s3"] = "local"
    basedir: str | None = None


class LoggingSettings(BaseModel):
    log_level: int = 10
    format: str = "%(name)s - %(asctime)s - %(levelname)s - %(message)s"


class ResourcesSettings(BaseModel):
    brands: str | None = None


class WebdriverSettings(BaseModel):
    chrome_binary_path: str | None = None
    chromedriver_path: str | None = None
    chrome_options: list[str] = []
    use_stealth: bool = True
    timeout_seconds: int = 30


class DatabaseSettings(BaseModel):
    url: str | None = None
    echo: bool = False


class HttpSettings(BaseModel):
    url: str | None = None
    client_type: Literal["requests", "httpx"] = "requests"
    headers: dict[str, str] = {}


class ListingScraperSettings(BaseModel):
    min_req_delay: float = 1.0
    max_req_delay: float = 4.0
    timeout: float = 20.0
    created_gte: Literal["-24+hours", "-7+days", "-30+days"] = "-7+days"

    @field_validator("created_gte")
    @classmethod
    def validate_created_gte(cls, v: str) -> str:
        if v not in ["-24+hours", "-7+days", "-30+days"]:
            raise ValueError(
                f"Invalid created_gte format: '{v}'. "
                "Must be one of: '-24+hours', '-7+days', '-30+days'"
            )
        return v


class VehicleScraperSettings(BaseModel):
    min_req_delay: float = 1.0
    max_req_delay: float = 4.0
    timeout: float = 20.0
    reinit_session_every: int = 500


class ScrapersSettings(BaseModel):
    listing_scraper: ListingScraperSettings
    vehicle_scraper: VehicleScraperSettings


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

    app_name: str = "carscout-pipe"
    app_version: str = version("carscout-pipe")
    environment: str = "local"
    debug: bool = False
    project_root: str = str(PROJECT_ROOT)

    file_service: FileServiceSettings
    logging: LoggingSettings
    resources: ResourcesSettings
    webdriver: WebdriverSettings
    http: HttpSettings
    database: DatabaseSettings
    scrapers: ScrapersSettings

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
