from typing import List, Dict
import requests

from .base import BaseScraper
from src.config import ConfigManager
from src.io.file_service import LocalFileService


class BrandsAndModelsScraper(BaseScraper):
    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService):
        super().__init__(config_manager, file_service)

    def scrape(self, brands: List[str]) -> List[Dict]:
        """Implementation of the abstract scrape method"""
        brands_data = self._scrape_brands(brands)
        return self._scrape_models(brands_data)

    def _scrape_brands(self, brands: List[str]) -> List[Dict]:
        """Scrape brands data for given brand slugs"""
        print("Collecting brands data ...")
        response = requests.get(
            f"{self.config_manager.base_url}/categories/{self.config_manager.config.api['category_id']}/brands",
            headers=self.config_manager.config.api['headers']
        )
        response.raise_for_status()
        response = response.json()
        brands_data = [b for b in response["data"] if b["slug"] in brands]
        print(f"{len(brands_data)} brands found.")
        return brands_data

    def _scrape_models(self, brands_data: List[Dict]) -> List[Dict]:
        """Scrape models data for given brands"""
        print("Collecting brand models ...")
        brands_and_models_data = []
        for bd in brands_data:
            response = requests.get(
                f"{self.config_manager.base_url}/categories/{self.config_manager.config.api['category_id']}/brands/{bd['id']}/models",
                headers=self.config_manager.config.api['headers']
            )
            response.raise_for_status()
            response = response.json()
            models_data = response["data"]
            expanded_models_data = []
            for md in models_data:
                if "models" in md:
                    expanded_models_data.extend(md["models"])
                else:
                    expanded_models_data.append(md)
            
            for md in expanded_models_data:
                brands_and_models_data.append({
                    "brand_id": bd["id"],
                    "brand_name": bd["name"],
                    "brand_slug": bd["slug"],
                    "model_id": md["id"],
                    "model_name": md["name"],
                    "model_slug": md["slug"],
                })
        print(f"Found {len(brands_and_models_data)} models.")
        return brands_and_models_data
