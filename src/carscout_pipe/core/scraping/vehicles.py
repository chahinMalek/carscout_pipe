from typing import Optional

from scrapy import Selector
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.data_models.vehicles import Vehicle
from src.carscout_pipe.core.exceptions import OlxPageNotFound
from src.carscout_pipe.core.scraping.requests import get_page_source
from src.carscout_pipe.core.scraping.vehicle_attributes import VEHICLE_ATTRIBUTE_SELECTORS
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)


def extract_vehicle_details(
        driver: WebDriver,
        listing: Listing,
        min_delay: int = 1,
        max_delay: int = 5,
        timeout_after: int = 10,
) -> Optional[Vehicle]:
    """Extract detailed vehicle information from a listing page."""
    try:
        page_source = get_page_source(driver, listing.url, min_delay=min_delay, max_delay=max_delay)
        selector = Selector(text=page_source)
        vehicle_data = listing.__dict__

        for attribute_name, attribute_selector in VEHICLE_ATTRIBUTE_SELECTORS.items():
            value = selector.xpath(attribute_selector.xpath).get()
            if attribute_selector.type == bool:
                value = True if value else False
            elif attribute_selector.type == str and isinstance(value, str):
                value = value.strip()
            vehicle_data[attribute_name] = value

        return Vehicle(**vehicle_data)

    except TimeoutException:
        logger.error(f"Error retrieving vehicle page {listing.url}: Timed out.")
    except OlxPageNotFound:
        logger.error(f"Error retrieving vehicle page {listing.url}: Not found.")
    except Exception as e:
        logger.error(f"Unexpected error occurred while extracting vehicle details {listing.url}: {e}")
        return None
