from logging import DEBUG

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth

from src.carscout_pipe.infra.logging import get_logger
from src.carscout_pipe.infra.utils import timeout


logger = get_logger(__name__, log_level=DEBUG)


def init_driver(timeout_seconds: int = 30) -> webdriver.Chrome:
    """
    Initialize Chrome WebDriver with stealth settings and timeout.

    Args:
        timeout_seconds: Maximum time to wait for driver initialization

    Returns:
        webdriver.Chrome: Initialized Chrome WebDriver

    Raises:
        TimeoutError: If driver initialization takes too long
        WebDriverException: If driver initialization fails
        Exception: If an unexpected error occurs
    """
    try:
        with timeout(timeout_seconds):
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            chrome_options.add_argument("--disable-search-engine-choice-screen")
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")

            driver = webdriver.Chrome(options=chrome_options)
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
        logger.error(
            f"WebDriver initialization timed out after {timeout_seconds} seconds"
        )
        raise
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during WebDriver initialization: {str(e)}")
        raise
