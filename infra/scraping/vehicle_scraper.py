from typing import Generator

from core.entities.listing import Listing
from core.entities.vehicle import Vehicle
from infra.factory.clients.http import HttpClientFactory
from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory
from infra.interfaces.http import HttpClient
from infra.scraping.base import Scraper


class VehicleScraper(Scraper):

    def __init__(
        self,
        logger_factory: LoggerFactory,
        webdriver_factory: WebdriverFactory,
        http_client_factory: HttpClientFactory,
        min_req_delay: float = 1.0,
        max_req_delay: float = 3.0,
        timeout: float = 10.0,
    ):
        super().__init__(logger_factory, webdriver_factory, http_client_factory)
        self._http_client: HttpClient | None = None
        self._min_req_delay = min_req_delay
        self._max_req_delay = max_req_delay
        self._timeout = timeout

    @property
    def scraper_id(self) -> str:
        return "vehicle_scraper"

    def run(self, listing: Listing) -> Vehicle | None:
        pass
