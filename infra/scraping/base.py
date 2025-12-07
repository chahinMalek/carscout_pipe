from abc import abstractmethod

from infra.factory.logger import LoggerFactory


class Scraper:
    def __init__(self, logger_factory: LoggerFactory):
        self._logger = logger_factory.create(self.scraper_id)

    @property
    @abstractmethod
    def scraper_id(self) -> str:
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
