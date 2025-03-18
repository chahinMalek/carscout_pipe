from logging import INFO
from typing import Dict, Optional

from scrapy import Selector

from carscout_pipe.attribute_selectors import ATTRIBUTE_SELECTORS
from carscout_pipe.data_models.vehicles.schema import Vehicle
from carscout_pipe.utils.logging import get_logger

logger = get_logger(__name__, log_level=INFO)


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


def parse_vehicle_info(selector: Selector) -> Dict:
    """
    Extract vehicle information from a page using the defined attribute selectors.
    
    Args:
        selector: Scrapy Selector for the vehicle page
        
    Returns:
        Dictionary containing the extracted vehicle data
    """
    params = {}
    for attribute, s in ATTRIBUTE_SELECTORS.items():
        value = selector.xpath(s.xpath).get()
        if s.type == bool:
            value = True if value else False
        elif s.type == str and isinstance(value, str):
            value = value.strip()
        params[attribute] = value
    vehicle = Vehicle.from_raw_dict(params)
    return vehicle.model_dump()
