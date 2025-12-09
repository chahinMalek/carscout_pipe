from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth

from infra.factory.logger import LoggerFactory
from infra.utils.timeout import timeout


class WebdriverFactory:
    def __init__(
        self,
        chrome_options: list[str],
        use_stealth: bool,
        logger_factory: LoggerFactory,
        timeout_seconds: int = 30,
        chrome_binary_path: str = None,
        chromedriver_path: str = None,
    ):
        self._chrome_options = chrome_options
        self._use_stealth = use_stealth
        self._timeout_seconds = timeout_seconds
        self._chrome_binary_path = chrome_binary_path
        self._chromedriver_path = chromedriver_path
        self._logger = logger_factory.create(__name__)

    def create(self) -> webdriver.Chrome:
        try:
            with timeout(self._timeout_seconds):
                chrome_options = Options()

                # Set chromium binary location if configured
                if self._chrome_binary_path:
                    chrome_options.binary_location = self._chrome_binary_path

                for option in self._chrome_options:
                    chrome_options.add_argument(option)

                # Create service with ChromeDriver path if configured
                service = None
                if self._chromedriver_path:
                    service = Service(executable_path=self._chromedriver_path)

                driver = webdriver.Chrome(service=service, options=chrome_options)

                if self._use_stealth:
                    stealth(
                        driver,
                        languages=["en-US", "en"],
                        vendor="Google Inc.",
                        platform="Win32",
                        webgl_vendor="Intel Inc.",
                        renderer="Intel Iris OpenGL Engine",
                        fix_hairline=True,
                    )
                return driver
        except TimeoutError:
            self._logger.error(
                f"WebDriver initialization timed out after {self._timeout_seconds} seconds"
            )
            raise
        except WebDriverException as e:
            self._logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
        except Exception as e:
            self._logger.error(f"An unexpected error occurred: {str(e)}")
            raise
