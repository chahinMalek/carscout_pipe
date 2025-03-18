import random
import signal
import time
from contextlib import contextmanager
from logging import DEBUG

from backoff import on_exception, expo
from requests import RequestException
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

from carscout_pipe.exceptions import OlxPageNotFound
from carscout_pipe.utils.logging import get_logger

logger = get_logger(__name__, log_level=DEBUG)


@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError("Timed out!")

    # Set the signal handler and a 5-second alarm
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Disable the alarm and restore the original handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


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
        logger.error(f"WebDriver initialization timed out after {timeout_seconds} seconds")
        raise
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during WebDriver initialization: {str(e)}")
        raise


@on_exception(
    expo,
    RequestException,
    max_tries=3,
    max_time=60,
    giveup=lambda e: isinstance(e, OlxPageNotFound),
)
def get_page_source(
        driver: webdriver.Chrome,
        url: str,
        min_delay: int = 0,
        max_delay: int = 0,
        timeout_after: int = 10,
):
    """
    Get the page source using the WebDriver with error handling and backoff.
    
    Args:
        driver: Chrome WebDriver instance
        url: URL to navigate to
        min_delay: Minimum delay before request in seconds
        max_delay: Maximum delay before request in seconds
        timeout_after: Maximum time to wait for page load in seconds
        
    Returns:
        Page source HTML as string
        
    Raises:
        TimeoutException: If page doesn't load within timeout
        OlxPageNotFound: If page is not found (404-like response)
        RequestException: For other request errors
    """
    try:
        request_delay = random.uniform(min_delay, max_delay)
        time.sleep(request_delay)
        driver.get(url)
        WebDriverWait(driver, timeout_after).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return driver.page_source
    except TimeoutException as err:
        patterns_404 = ["Oprostite, ne možemo pronaći ovu stranicu", "Nema rezultata za traženi pojam"]
        if any(p in driver.page_source for p in patterns_404):
            raise OlxPageNotFound(url)  # raise different error to prevent backoff
        raise err  # re-raise the error to continue backoff
