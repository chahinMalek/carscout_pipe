import random
import time
from logging import INFO
from typing import Optional

from backoff import on_exception, expo
from requests import RequestException
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from src.carscout_pipe.core.exceptions import OlxPageNotFound
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__, log_level=INFO)

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


def get_next_page(page_source: str) -> Optional[str]:
    """
    Parse the page source to find the next page number.

    Args:
        page_source: HTML content of the current page

    Returns:
        Next page number as a string, or None if there's no next page
    """
    logger.debug("Retrieving next page ...")
    selector = Selector(text=page_source)
    pagination_item = selector.xpath("//div[@class='olx-pagination-wrapper']").get()
    if not pagination_item:
        logger.debug("No pagination item found")
        return None
    next_page_xpath = "normalize-space(//li[@class='active']/following-sibling::li[1]/text())"
    next_page = Selector(text=pagination_item).xpath(next_page_xpath).get()
    next_page = next_page or None
    logger.debug(f"Next page: {next_page}")
    return next_page
