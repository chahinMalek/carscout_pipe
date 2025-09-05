import os
import random
import sys
import uuid
from datetime import datetime
from functools import partial
from logging import DEBUG
from typing import Dict, List, Optional, Tuple, Callable, Any, Iterator

import pandas as pd
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from tqdm import tqdm

from carscout_pipe.exceptions import OlxPageNotFound
from carscout_pipe.utils.logging import get_logger
from carscout_pipe.utils.scraping import get_next_page, parse_vehicle_info
from carscout_pipe.utils.webdriver import init_driver, get_page_source

logger = get_logger(__name__, log_level=DEBUG)


# Configuration functions
def get_config() -> Dict[str, Any]:
    """Return the configuration for the scraper."""
    return {
        "brands_path": "./data/brands.csv",
        "request_min_delay_seconds": 3,
        "request_max_delay_seconds": 5,
        "wait_time_seconds": 10,
        "url_template": (
            "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
            "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
        ),
        "run_id": str(uuid.uuid4()),
    }


def setup_output_dir(run_id: str) -> Tuple[str, str]:
    """Create output directory and return path templates."""
    output_dir = f"./data/output/{run_id}/"
    os.makedirs(output_dir, exist_ok=True)
    filename_template = "part_{idx:08}.csv"
    output_partfile_template = os.path.join(output_dir, filename_template)
    return output_dir, output_partfile_template


def load_brands(brands_path: str) -> List[Dict[str, Any]]:
    """Load brands from CSV file."""
    return pd.read_csv(brands_path).to_dict(orient="records")


# Core scraping functions
def generate_listing_urls(
    driver: webdriver.Chrome,
    brand_id: int,
    url_template: str,
    request_config: Dict[str, int]
) -> Iterator[Tuple[str, List[str]]]:
    """
    Generator that yields a tuple of (page_url, listing_urls) for each page
    of listings for a brand.
    """
    next_page = "1"
    
    while next_page:
        url = url_template.format(brand_id=brand_id, page=next_page)
        logger.info(f"Scraping listings from: {url}")
        
        try:
            articles_page_source = get_page_source(
                driver, url,
                min_delay=request_config["min_delay"],
                max_delay=request_config["max_delay"],
                timeout_after=request_config["timeout"],
            )
            
            selector = Selector(text=articles_page_source)
            listing_urls_xpath = "//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]//a/@href"
            listing_urls = selector.xpath(listing_urls_xpath).getall()
            listing_urls = [f"https://olx.ba{url_suffix}" for url_suffix in listing_urls]
            random.shuffle(listing_urls)
            
            # Get next page for the next iteration
            next_page_val = get_next_page(articles_page_source)
            
            # Yield the current page's data and update for next iteration
            yield url, listing_urls
            next_page = next_page_val
            
        except TimeoutException:
            logger.error(f"Error retrieving listings page {url}: Timed out.")
            break
        except OlxPageNotFound:
            logger.error(f"Error retrieving listings page {url}: Not found.")
            break
        except Exception as err:
            logger.error(f"Unexpected error occurred while scraping listings page {url}: {err}")
            break


def scrape_vehicle(
    driver: webdriver.Chrome,
    listing_url: str,
    request_config: Dict[str, int],
    run_id: str
) -> Optional[Dict[str, Any]]:
    """Scrape a single vehicle listing and return its data."""
    try:
        page_source = get_page_source(
            driver, listing_url,
            min_delay=request_config["min_delay"],
            max_delay=request_config["max_delay"],
            timeout_after=request_config["timeout"],
        )
        selector = Selector(text=page_source)
        vehicle = parse_vehicle_info(selector)
        vehicle["url"] = listing_url
        vehicle["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vehicle["run_id"] = run_id
        return vehicle
    except TimeoutException:
        logger.error(f"Error retrieving vehicle page {listing_url}: Timed out.")
    except OlxPageNotFound:
        logger.error(f"Error retrieving vehicle page {listing_url}: Not found.")
    except Exception as err:
        logger.error(f"Unexpected error occurred while scraping vehicle {listing_url}: {err}")
    return None


def scrape_vehicles(
    driver: webdriver.Chrome,
    listing_urls: List[str],
    request_config: Dict[str, int],
    run_id: str
) -> List[Dict[str, Any]]:
    """Scrape all vehicles from a list of listing URLs."""
    if not listing_urls:
        return []
    
    # Create a partial function with fixed parameters
    scrape_fn = partial(
        scrape_vehicle, 
        driver=driver, 
        request_config=request_config, 
        run_id=run_id
    )
    
    vehicles = []
    pbar = tqdm(listing_urls, desc="Processing listings", file=open(os.devnull, 'w'))
    
    for listing_url in pbar:
        vehicle = scrape_fn(listing_url=listing_url)
        if vehicle:
            vehicles.append(vehicle)
        logger.info(str(pbar))
        
    pbar.close()
    logger.debug("All vehicles from the page retrieved successfully.")
    return vehicles


def save_batch(vehicles: List[Dict[str, Any]], output_template: str, idx: int) -> int:
    """Save a batch of vehicles to a CSV file and return the next index."""
    if not vehicles:
        return idx
    
    try:
        output_path = output_template.format(idx=idx)
        logger.debug(f"Saving batch into `{output_path}` ...")
        df = pd.DataFrame(vehicles)
        df.to_csv(output_path, index=False)
        logger.debug(f"Batch saving successful.")
        return idx + 1
    except Exception as err:
        logger.error(f"Error occurred while saving batch: {err}")
        return idx


def process_brand(
    driver: webdriver.Chrome,
    brand_data: Dict[str, Any],
    config: Dict[str, Any],
    output_template: str,
    idx: int
) -> int:
    """Process all pages for a single brand and return the next global index."""
    brand_id = brand_data["brand_id"]
    request_config = {
        "min_delay": config["request_min_delay_seconds"],
        "max_delay": config["request_max_delay_seconds"],
        "timeout": config["wait_time_seconds"]
    }
    
    # Generator that yields (page_url, listing_urls) for each page
    page_listings = generate_listing_urls(
        driver, 
        brand_id, 
        config["url_template"], 
        request_config
    )
    
    current_idx = idx
    for _, listing_urls in page_listings:
        vehicles = scrape_vehicles(driver, listing_urls, request_config, config["run_id"])
        current_idx = save_batch(vehicles, output_template, current_idx)
        
    return current_idx


def main() -> None:
    """Main entry point with functional approach."""
    config = get_config()
    logger.debug("Starting process with parameters:")
    logger.debug(f"brands_path={config['brands_path']}")
    logger.debug(f"request_min_delay_seconds={config['request_min_delay_seconds']}")
    logger.debug(f"request_max_delay_seconds={config['request_max_delay_seconds']}")
    logger.debug(f"wait_time_seconds={config['wait_time_seconds']}")
    logger.debug(f"run_id={config['run_id']}")
    
    # Setup
    _, output_template = setup_output_dir(config["run_id"])
    brands = load_brands(config["brands_path"])
    
    driver = None
    try:
        logger.debug("Initializing WebDriver")
        driver = init_driver()
        
        # Process each brand using a fold/reduce pattern
        global_idx = 0
        for brand_data in brands:
            global_idx = process_brand(driver, brand_data, config, output_template, global_idx)
            
    except (TimeoutError, WebDriverException) as e:
        logger.error(f"Failed to initialize WebDriver: {e}. Exiting...")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error while closing WebDriver: {str(e)}")


if __name__ == "__main__":
    main() 