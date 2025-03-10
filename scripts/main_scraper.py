import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime
from typing import Dict

import pandas as pd
from backoff import on_exception, expo
from requests import RequestException
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from tqdm import tqdm

from src.exceptions import OlxPageNotFound
from src.xpaths import ATTRIBUTE_SELECTORS
from src.vehicle_model import Vehicle

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def init_driver():
    logger.debug("Initializing WebDriver")
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
    try:
        request_delay = random.uniform(min_delay, max_delay)
        time.sleep(request_delay)
        driver.get(url)
        # WebDriverWait(driver, timeout_after).until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "articles"))
        # )
        # WebDriverWait(driver, timeout_after).until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "required-attributes"))
        # )
        WebDriverWait(driver, timeout_after).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return driver.page_source
    except TimeoutException as err:
        patterns_404 = ["Oprostite, ne možemo pronaći ovu stranicu", "Nema rezultata za traženi pojam"]
        if any(p in driver.page_source for p in patterns_404):
            raise OlxPageNotFound(url) # raise different error to prevent backoff
        raise err  # re-raise the error to continue backoff


def get_next_page(page_source: str):
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


if __name__ == '__main__':

    brands_path = "../data/brands.csv"
    logger.debug(f"{brands_path=}")
    brands = pd.read_csv(brands_path).to_dict(orient="records")

    driver = init_driver()
    url_template = (
        "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
        "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
    )

    request_min_delay_seconds = 3
    request_max_delay_seconds = 5
    wait_time_seconds = 10
    run_id = str(uuid.uuid4())

    logger.debug(f"{request_min_delay_seconds=}")
    logger.debug(f"{request_max_delay_seconds=}")
    logger.debug(f"{wait_time_seconds=}")
    logger.debug(f"{run_id=}")

    output_dir = f"../data/output/{run_id}/"
    os.makedirs(output_dir, exist_ok=True)
    filename_template = "part_{idx:08}.csv"
    output_partfile_template = os.path.join(output_dir, filename_template)
    global_idx = 0

    for brand_data in brands:
        brand_id = brand_data["brand_id"]
        next_page = "1"

        while next_page:
            url = url_template.format(brand_id=brand_id, page=next_page)
            logger.info(f"Scraping listings from: {url}")
            listing_urls = []

            try:
                articles_page_source = get_page_source(
                    driver, url,
                    min_delay=request_min_delay_seconds,
                    max_delay=request_min_delay_seconds,
                    timeout_after=wait_time_seconds,
                )
                selector = Selector(text=articles_page_source)
                listing_urls_xpath = "//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]//a/@href"
                listing_urls = selector.xpath(listing_urls_xpath).getall()
                listing_urls = [f"https://olx.ba{url_suffix}" for url_suffix in listing_urls]
                random.shuffle(listing_urls)
            except TimeoutException:
                logger.error(f"Error retrieving listings page {url}: Timed out.")
            except OlxPageNotFound as err:
                logger.error(f"Error retrieving listings page {url}: Not found.")
            except Exception as err:
                logger.error(f"Unexpected error occurred while scraping listings page {url}: {err}")
            logger.debug("Listings retrieved successfully.")
            logger.debug(f"{len(listing_urls)=}")

            if len(listing_urls) > 0:
                vehicles = []
                pbar = tqdm(listing_urls, desc=f"Processing listings", file=open(os.devnull, 'w'))
                for listing_url in pbar:
                    try:
                        page_source = get_page_source(
                            driver, listing_url,
                            min_delay=request_min_delay_seconds,
                            max_delay=request_min_delay_seconds,
                            timeout_after=wait_time_seconds,
                        )
                        selector = Selector(text=page_source)
                        vehicle = parse_vehicle_info(selector)
                        vehicle["url"] = listing_url
                        vehicle["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        vehicle["run_id"] = run_id
                        vehicles.append(vehicle)
                    except TimeoutException:
                        logger.error(f"Error retrieving vehicle page {url}: Timed out.")
                    except OlxPageNotFound as err:
                        logger.error(f"Error retrieving vehicle page {url}: Not found.")
                    except Exception as err:
                        logger.error(f"Unexpected error occurred while scraping vehicle {listing_url}: {err}")
                    finally:
                        logger.info(str(pbar))
                pbar.close()
                logger.debug("All vehicles from the page retrieved successfully.")

                try:
                    output_path = output_partfile_template.format(idx=global_idx)
                    logger.debug(f"Saving batch into `{output_path}` ...")
                    df = pd.DataFrame(vehicles)
                    df.to_csv(output_path, index=False)
                    logger.debug(f"Batch saving successful.")
                    global_idx += 1
                except Exception as err:
                    logger.error(f"Error occurred while saving batch: {err}")

            try:
                next_page = get_next_page(articles_page_source)
            except Exception as err:
                logger.error(f"Error occurred while parsing next page: {err}")
                break

    driver.quit()
