import yaml
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel


class Config(BaseModel):
    api: Dict
    paths: Dict
    selenium: Dict
    db: Dict

    @staticmethod
    def load(path: str) -> 'Config':
        """Load configuration from a specified YAML file."""
        with open(path, 'r') as file:
            config_data = yaml.safe_load(file)
        return Config(**config_data)

    @classmethod
    def local(cls) -> 'Config':
        BASE_PATH = Path(__file__).parent.parent / 'configs' / 'local.yml'
        return cls.load(str(BASE_PATH))


class ConfigManager:
    def __init__(self, config: Config):
        self.config = config

    @staticmethod
    def from_local() -> 'ConfigManager':
        return ConfigManager(Config.local())

    @property
    def base_path(self) -> str:
        return self.config.paths['base_path']

    @property
    def brands_and_models_path(self) -> str:
        return str(Path(self.base_path) / self.config.paths['brands_and_models_prefix'])

    @property
    def listings_path(self) -> str:
        return str(Path(self.base_path) / self.config.paths['listings_prefix'])

    @property
    def vehicles_path(self) -> str:
        return str(Path(self.base_path) / self.config.paths['vehicles_prefix'])

    @property
    def base_url(self) -> str:
        return self.config.api['base_url']

    @property
    def chrome_options(self) -> List[str]:
        return self.config.selenium['chrome_options']

    @property
    def db_connection_params(self) -> Dict:
        return {
            "host": self.config.db['host'],
            "database": self.config.db['database'],
        }

    @property
    def db_collections(self) -> Dict:
        return self.config.db['collections']
