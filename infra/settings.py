from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LoggingSettings(BaseModel):
    log_level: int = 10


class SQLiteSettings(BaseModel):
    url: str
    echo: bool = False


class ResourcesSettings(BaseModel):
    brands: str


class WebdriverSettings(BaseModel):
    chrome_binary_path: str | None = None
    chromedriver_path: str | None = None


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",  # Allows loading values only from YAML if not in Env
    )

    app_name: str = "carscout-pipe"
    app_version: str = version(app_name or "carscout-pipe")
    environment: str = "local"
    debug: bool = False
    project_root: str = str(PROJECT_ROOT)

    logging: LoggingSettings
    database: SQLiteSettings
    resources: ResourcesSettings
    webdriver: WebdriverSettings
    scrapers: ScrapersSettings
