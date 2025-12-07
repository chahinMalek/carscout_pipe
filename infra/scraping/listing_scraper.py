import random
import time
from datetime import datetime
from typing import Generator

from backoff import on_exception, expo
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from core.entities.brand import Brand
from core.entities.listing import Listing
from core.exceptions import PageNotFoundError
from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory
from infra.scraping.base import Scraper


class ListingScraper(Scraper):
    def __init__(
        self,
        logger_factory: LoggerFactory,
        webdriver_factory: WebdriverFactory,
        min_req_delay: float = 1.0,
        max_req_delay: float = 3.0,
        timeout: float = 10.0,
    ):
        super().__init__(logger_factory)
        self._webdriver_factory = webdriver_factory
        self._min_req_delay = min_req_delay
        self._max_req_delay = max_req_delay
        self._timeout = timeout

    @property
    def scraper_id(self) -> str:
        return "listing_scraper"

    def run(self, brand: Brand) -> Generator[Listing, None, None]:
        driver = None
        try:
            driver = self._webdriver_factory.create()
            yield from self.scrape_listings(driver, brand)
        except Exception as err:
            self._logger.error(
                f"Unexpected error occurred during scraping brand_id={brand.id}: {err}"
            )
        finally:
            if driver:
                driver.quit()

    def scrape_listings(
        self,
        driver: webdriver.Chrome,
        brand: Brand,
    ) -> Generator[list[Listing], None, None]:
        next_page = "1"
        url_template = (
            "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
            "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
        )
        while next_page:
            url = url_template.format(brand_id=brand.id, page=next_page)
            self._logger.info(f"Scraping listings from: {url}")
            try:
                self._logger.debug(f"Retrieving page source: {url}")
                page_source = self._get_page_source(url, driver)
                self._logger.debug(f"Extracting listings: {url}")
                page_listings = self._extract_listings(page_source)
                yield from page_listings
                self._logger.debug(f"Retrieving next page: {url}")
                next_page = self._get_next_page(page_source)
            except Exception as err:
                self._logger.error(
                    f"Unexpected error occurred during scraping listings from url={url}: {err}"
                )
        self._logger.debug(f"No more pages left. Last page url: {url}")

    @on_exception(
        expo,
        Exception,
        max_tries=3,
        max_time=60,
        giveup=lambda e: isinstance(e, PageNotFoundError),
    )
    def _get_page_source(self, url: str, driver: webdriver.Chrome) -> str:
        try:
            req_delay = random.uniform(self._min_req_delay, self._max_req_delay)
            self._logger.debug(f"Sleeping before request for {req_delay:.4f} seconds.")
            time.sleep(req_delay)
            driver.get(url)
            WebDriverWait(driver, self._timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            if self._check_page_unk(driver.page_source):
                raise PageNotFoundError(url)
            return driver.page_source
        except TimeoutException as err:
            if self._check_page_unk(driver.page_source):
                raise PageNotFoundError(url) from err
            raise err  # re-raise the error to continue backoff

    def _check_page_unk(self, page_source: str) -> bool:
        patterns_404 = [
            "Oprostite, ne možemo pronaći ovu stranicu",
            "Nema rezultata za traženi pojam",
        ]
        page_not_exists = any(p in page_source for p in patterns_404)
        return page_not_exists

    def _extract_listings(self, page_source: str) -> list[Listing]:
        page_selector = Selector(text=page_source)
        listings_selector = "//a[starts-with(@href, '/artikal/')]"
        listing_cards = page_selector.xpath(listings_selector).getall()
        listings = []
        for card in listing_cards:
            card_selector = Selector(text=card)
            url_suffix = card_selector.xpath("//@href").get().strip()
            listing_url = f"https://olx.ba{url_suffix}"
            listing_id = listing_url.split("/")[-1]
            title_selector = "//h1[contains(@class, 'main-heading')]/text()"
            listing_title = card_selector.xpath(title_selector).get().strip()
            price_selector = "//div[contains(@class, 'price-wrap')]//span[contains(@class, 'smaller')]/text()"
            listing_price = card_selector.xpath(price_selector).get().strip()
            listings.append(
                Listing(
                    id=listing_id,
                    url=listing_url,
                    title=listing_title,
                    price=listing_price,
                    visited_at=datetime.now(),
                )
            )
        return listings

    def _get_next_page(self, page_source: str) -> str | None:
        selector = Selector(text=page_source)
        pagination_selector = "//div[@class='olx-pagination-wrapper']"
        pagination_item = selector.xpath(pagination_selector).get()
        if not pagination_item:
            self._logger.debug("No pagination item found...")
            return None
        next_page_selector = (
            "normalize-space(//li[@class='active']/following-sibling::li[1]/text())"
        )
        next_page = Selector(text=pagination_item).xpath(next_page_selector).get()
        return next_page or None
