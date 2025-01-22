from typing import List, Dict
from tqdm import tqdm
from scrapy import Selector
import time

from src.config import ConfigManager
from src.io.file_service import LocalFileService
from src.scrapers.selenium_base import SeleniumScraper
from src.data_models.listing import VehicleListing


class ListingsScraper(SeleniumScraper):
    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService, max_pages: int = 5):
        super().__init__(config_manager, file_service)
        self.search_params = {
            "attr": "",
            "attr_encoded": "1",
            "category_id": config_manager.config.api["category_id"],
            "created_gte": "-1+month"
        }
        self.max_pages = max_pages

    def scrape(self, input_data: List[Dict]) -> List[Dict]:
        """Scrape listings for given brands and models data"""
        all_listings: List[Dict] = []

        try:
            for row in tqdm(input_data, total=len(input_data)):
                brand_id = row["brand_id"]
                model_id = row["model_id"]
                all_listings.extend(self._scrape_brand_model(brand_id, model_id))

        finally:
            self.cleanup()

        return [listing.model_dump() for listing in all_listings]

    def _scrape_brand_model(self, brand_id: str, model_id: str) -> List[Dict]:
        """Scrape listings for a specific brand and model combination"""
        listings = []
        
        for page in range(1, self.max_pages + 1):
            params = self.search_params | {
                "brand": brand_id,
                "models": model_id,
                "brands": brand_id,
                "page": page
            }
            url = "https://olx.ba/pretraga?" + "&".join([f"{k}={v}" for k, v in params.items()])
            print(f"INFO - Scraping: {url} ...")
            
            page_listings = self._parse_listings(url)
            if not page_listings:
                break
                
            listings.extend(page_listings)
            
        return listings

    def _parse_listings(self, url: str) -> List[VehicleListing]:
        """Parse vehicle listings from a given URL"""
        self.driver.get(url)
        time.sleep(1)
        selector = Selector(text=self.driver.page_source)

        listings = selector.xpath("//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]").getall()
        xpaths = {
            "title": "//div[contains(@class, 'listing-card')]//h1[contains(@class, 'main-heading')]//text()",
            "price": "//div[contains(@class, 'price-wrap')]//span[contains(@class, 'smaller')]//text()",
            "article_id": "//a[starts-with(@href, '/artikal')]//@href"
        }
        
        response = []
        for listing in listings:
            try:
                listing_data = {}
                for attr, xpath in xpaths.items():
                    value = Selector(text=listing).xpath(xpath).get()
                    if value is not None:
                        value = value.strip()
                    listing_data[attr] = value
                
                if listing_data["article_id"]:
                    listing_data["article_id"] = listing_data["article_id"].split("/")[-1]
                    listing_data["url"] = f"https://olx.ba/artikal/{listing_data['article_id']}"
                    response.append(VehicleListing(**listing_data))
            except Exception as err:
                print(f"Error while scraping listing: {err}")
                
        return response
