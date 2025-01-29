from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path
import pandas as pd

from src.config import ConfigManager
from src.io.file_service import LocalFileService


class BaseScraper(ABC):
    """Base class for all scrapers"""
    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService):
        self.config_manager = config_manager
        self.file_service = file_service

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Main scraping method to be implemented by concrete scrapers"""
        pass

    def cleanup(self):
        """Clean up resources if needed"""
        pass 