from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options

from src.scrapers.base import BaseScraper
from src.config import ConfigManager
from src.io.file_service import LocalFileService


class SeleniumScraper(BaseScraper):
    """Base class for scrapers that use Selenium"""

    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService):
        super().__init__(config_manager, file_service)
        self.driver = self._init_driver()

    def _init_driver(self) -> WebDriver:
        """Initialize Chrome WebDriver with given options"""
        chrome_options = Options()
        for option in self.config_manager.chrome_options:
            chrome_options.add_argument(option)
        return webdriver.Chrome(options=chrome_options)

    def cleanup(self):
        """Clean up Selenium resources"""
        super().cleanup()
        if hasattr(self, "driver"):
            self.driver.quit()
