from abc import abstractmethod

from infra.factory.clients.http import HttpClientFactory
from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory


class Scraper:
    def __init__(
        self,
        logger_factory: LoggerFactory,
        webdriver_factory: WebdriverFactory,
        http_client_factory: HttpClientFactory,
    ):
        self._logger = logger_factory.create(self.scraper_id)
        self._webdriver_factory = webdriver_factory
        self._http_client_factory = http_client_factory

    @property
    @abstractmethod
    def scraper_id(self) -> str:
        pass
