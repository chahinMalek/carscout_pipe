import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


class DatabaseSettings(BaseModel):
    url: str
    path: Optional[str] = None
    echo: bool = False


class Settings(BaseModel):
    database: DatabaseSettings
    environment: str = "local"
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from YAML configuration file."""
        if config_path is None:
            # Default to local environment config
            config_path = Path(__file__).parent / "environments" / "local.yml"
        
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        return cls(**config_data)


# Global settings instance
settings = Settings.load_from_file()