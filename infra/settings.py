from importlib.metadata import version
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LoggingSettings(BaseModel):
    log_level: int = 10


class SQLiteSettings(BaseModel):
    url: str
    echo: bool = False


class RedisSettings(BaseModel):
    url: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )

    app_name: str = "carscout-pipe"
    app_version: str = version(app_name)
    environment: str = "local"
    debug: bool = False
    project_root: str = str(PROJECT_ROOT)

    logging: LoggingSettings
    redis: RedisSettings
    database: SQLiteSettings
