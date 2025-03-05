import os
import time
from typing import List, Dict

from backoff import on_exception, expo
from requests.exceptions import RequestException
from scrapy import Selector
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm

from src.config import ConfigManager
from src.data_models.listing import VehicleListing
from src.exceptions import OlxPageNotFound
from src.io.file_service import LocalFileService
from src.scrapers.selenium_base import SeleniumScraper
from src.utils.logging import get_logger


class BrandListingsScraper(SeleniumScraper):
    def __init__(
        self,
        config_manager: ConfigManager,
        file_service: LocalFileService,
        max_pages: int = 5,
        log_level: str = "INFO",
    ):
        super().__init__(config_manager, file_service)
        self._search_params = {
            "attr": "",
            "attr_encoded": "1",
            "category_id": config_manager.config.api["category_id"],
            "created_gte": "-1+month",
            "models": "",
        }
        self._max_pages = max_pages
        self._patience = 3
        self._logger = get_logger(__name__, log_level)

    def scrape(self, brand_id: int) -> List[Dict]:
        """Scrape listings for given brands and models data"""
        all_listings: List[Dict] = []
        pbar = tqdm(
            range(1, self._max_pages + 1),
            total=self._max_pages,
            desc=f"Processing listings (brand_id={brand_id})",
            file=open(os.devnull, 'w'),
        )
        for page in pbar:
            data_retrieved = False
            for attempt in range(1, self._patience + 1):
                params = self._search_params | {
                    "brand": brand_id,
                    "brands": brand_id,
                    "page": page,
                }
                url = "https://olx.ba/pretraga?" + "&".join(
                    [f"{k}={v}" for k, v in params.items()]
                )
                self._logger.debug(f"Scraping {url} (attempt {attempt} of {self._patience})...")
                page_response = self._scrape_one(url)
                if not page_response or len(page_response) == 0:
                    continue
                all_listings.extend(page_response)
                data_retrieved = True
                break
            if not data_retrieved:
                self._logger.error("No data retrieved for brand_id=%s, page=%s", brand_id, page)
                break
            self._logger.info(str(pbar))
        pbar.close()
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
            self._logger.error(f"Error retrieving listings page {url}: Timed out.")
        except OlxPageNotFound as err:
            self._logger.error(err)
        except Exception as err:
            self._logger.error(f"Unexpected error scraping listings page {url}: {err}")
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
            patterns_404 = ["Oprostite, ne možemo pronaći ovu stranicu", "Nema rezultata za traženi pojam"]
            if any(p in self.driver.page_source for p in patterns_404):
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
                listing_data[attr] = value.strip() if value else None
        
            if listing_data.get("article_id"):
                article_id = listing_data["article_id"].split("/")[-1]
                listing_data["article_id"] = article_id
                listing_data["url"] = f"https://olx.ba/artikal/{article_id}"
                try:
                    response.append(VehicleListing(**listing_data))
                except Exception as e:
                    self._logger.error(f"Error creating VehicleListing object: {e}")
        
        return response
