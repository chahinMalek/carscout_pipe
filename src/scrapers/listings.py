from typing import List, Dict
from tqdm import tqdm
from scrapy import Selector
import time
from requests.exceptions import RequestException
from backoff import on_exception, expo
from selenium.common.exceptions import TimeoutException

from src.config import ConfigManager
from src.io.file_service import LocalFileService
from src.scrapers.selenium_base import SeleniumScraper
from src.data_models.listing import VehicleListing
from src.exceptions import OlxPageNotFound


class ListingsScraper(SeleniumScraper):
    def __init__(
        self,
        config_manager: ConfigManager,
        file_service: LocalFileService,
        max_pages: int = 5,
    ):
        super().__init__(config_manager, file_service)
        self._search_params = {
            "attr": "",
            "attr_encoded": "1",
            "category_id": config_manager.config.api["category_id"],
            "created_gte": "-1+month",
        }
        self._max_pages = max_pages
        self._patience = 3

    def scrape(self, input_data: List[Dict]) -> List[Dict]:
        """Scrape listings for given brands and models data"""
        all_listings: List[Dict] = []

        for row in tqdm(input_data, total=len(input_data)):
            patience = self._patience
            for page in range(1, self._max_pages + 1):
                params = self._search_params | {
                    "brand": row["brand_id"],
                    "models": row["model_id"],
                    "brands": row["brand_id"],
                    "page": page,
                }
                url = "https://olx.ba/pretraga?" + "&".join(
                    [f"{k}={v}" for k, v in params.items()]
                )
                print(f"INFO - Scraping: {url} with patience={patience}...")
                page_response = self._scrape_one(url)
                if not page_response or len(page_response) == 0:
                    patience -= 1
                    if patience <= 0:
                        break
                else:
                    all_listings.extend(page_response)
                    patience = self._patience

        return [listing.model_dump() for listing in all_listings]

    def _scrape_one(self, url: str) -> List[VehicleListing]:
        """Scrape listings for a specific URL"""
        response = []
        try:
            if not self.initialized:
                self.driver = self.init_driver()
            response = self._parse_listings_page(url)
            return response
        except TimeoutException:
            print(f"Error retrieving listings page {url}: Timed out.")
        except OlxPageNotFound as err:
            print(err)
        except Exception as err:
            print(f"Unexpected error scraping listings page {url}: {err}")
        finally:
            self.cleanup()
        return response

    @on_exception(expo, RequestException, max_tries=3, max_time=60)
    def _parse_listings_page(self, url: str) -> List[VehicleListing]:
        """Parse vehicle listings from a given URL"""
        try:
            self.driver.get(url)
            time.sleep(1)
            selector = Selector(text=self.driver.page_source)
            listings = selector.xpath(
                "//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]"
            ).getall()

        except TimeoutException as err:
            if "Oprostite, ne možemo pronaći ovu stranicu" in self.driver.page_source:
                raise OlxPageNotFound(url) # raise different error to prevent backoff
            raise err  # re-raise the error to continue backoff

        xpaths = {
            "title": "//div[contains(@class, 'listing-card')]//h1[contains(@class, 'main-heading')]//text()",
            "price": "//div[contains(@class, 'price-wrap')]//span[contains(@class, 'smaller')]//text()",
            "article_id": "//a[starts-with(@href, '/artikal')]//@href",
        }

        response = []
        for listing in listings:
            listing_data = {}
            for attr, xpath in xpaths.items():
                value = Selector(text=listing).xpath(xpath).get()
                if value is not None:
                    value = value.strip()
                listing_data[attr] = value

            if listing_data["article_id"]:
                listing_data["article_id"] = listing_data["article_id"].split("/")[-1]
                listing_data["url"] = (
                    f"https://olx.ba/artikal/{listing_data['article_id']}"
                )
                response.append(VehicleListing(**listing_data))

        return response
