import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import sqlite3

from backoff import on_exception, expo
from requests import RequestException
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from tqdm import tqdm

from carscout_pipe.exceptions import OlxPageNotFound
from carscout_pipe.attribute_selectors import ATTRIBUTE_SELECTORS
from carscout_pipe.data_models.vehicles.schema import Vehicle

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
    patterns_404 = ["Oprostite, ne možemo pronaći ovu stranicu", "Nema rezultata za traženi pojam"]
    try:
        request_delay = random.uniform(min_delay, max_delay)
        time.sleep(request_delay)
        driver.get(url)
        WebDriverWait(driver, timeout_after).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        if any(p in driver.page_source for p in patterns_404):
            raise OlxPageNotFound(url)
        return driver.page_source

    except TimeoutException as err:
        if any(p in driver.page_source for p in patterns_404):
            raise OlxPageNotFound(url) # raise different error to prevent backoff
        raise err  # re-raise the error to continue backoff


def parse_vehicle_info(driver, url: str) -> Optional[Dict]:
    try:
        page_source = get_page_source(
            driver, v["url"],
            min_delay=request_min_delay_seconds,
            max_delay=request_min_delay_seconds,
            timeout_after=wait_time_seconds,
        )
        selector = Selector(text=page_source)
        params = {}
        for attribute, s in ATTRIBUTE_SELECTORS.items():
            value = selector.xpath(s.xpath).get()
            if s.type == bool:
                value = True if value else False
            elif s.type == str and isinstance(value, str):
                value = value.strip()
            params[attribute] = value
        params["url"] = url
        params["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vehicle = Vehicle.from_raw_dict(params)
        if vehicle.sold:
            logger.debug(f"Encountered sold vehicle: {vehicle.url}")
        return vehicle.model_dump()

    except OlxPageNotFound:
        logger.error(f"Error retrieving vehicle page {url}: Not found.")
        logger.debug(f"Encountered inactive vehicle: {url}")
        return Vehicle.inactive_from_url(url).model_dump()

    except Exception as err:
        logger.error(f"Error retrieving vehicle page {url}: {err}")
        return None


def find_vehicles_to_rescrape(run_id: str) -> List[Dict]:
    """
    Find all urls that were part of a previous run and were not scraped in the current run.
    Results are required to be still active and not sold at the time of their latest processing.
    """
    conn = sqlite3.connect("./data/carscout.db")
    results = []
    try:
        cursor = conn.cursor()
        query = """
        WITH
        target_run AS (
            SELECT * FROM vehicles WHERE run_id = ?
        ),
        candidates AS (
            SELECT
            *
            FROM vehicles
            WHERE scraped_at < (SELECT MIN(scraped_at) FROM target_run)
                AND url NOT IN (SELECT DISTINCT url FROM target_run)
        ),
        latest_versions AS (
            SELECT c.*
            FROM candidates c
            JOIN (SELECT url, MAX(scraped_at) AS latest_scraped_at FROM candidates GROUP BY url) lv
            ON c.url = lv.url AND c.scraped_at = lv.latest_scraped_at
        )
        SELECT DISTINCT article_id, url, run_id, active FROM latest_versions
        WHERE active = 1 AND sold = 0;
        """
        cursor.execute(query, (run_id,))
        results = cursor.fetchall()

    except Exception as err:
        logger.error(f"Error initializing database: {err}")
    finally:
        conn.close()

    return pd.DataFrame(results, columns=["article_id", "url", "run_id", "active"]).to_dict(orient="records")


def generate_batches(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


if __name__ == '__main__':

    # todo: replace with most recent run_id
    run_id = 'ae7deaf6-9d1d-4565-bb38-487b5f9cafd8'
    batch_size = 40
    request_min_delay_seconds = 3
    request_max_delay_seconds = 5
    wait_time_seconds = 10

    logger.debug(f"{request_min_delay_seconds=}")
    logger.debug(f"{request_max_delay_seconds=}")
    logger.debug(f"{wait_time_seconds=}")
    logger.debug(f"{run_id=}")

    vehicles = find_vehicles_to_rescrape(run_id)



    logger.info(f"Number of vehicles to process: {len(vehicles)}")
    random.shuffle(vehicles)
    batches = generate_batches(vehicles, batch_size)

    output_dir = f"./data/output/{run_id}/"
    os.makedirs(output_dir, exist_ok=True)
    filename_template = "part_{idx:08}.csv"
    output_partfile_template = os.path.join(output_dir, filename_template)

    # todo: replace with the actual next global idx of the provided run_id
    global_idx = 500
    driver = init_driver()
    pbar = tqdm(total=len(vehicles), desc=f"Processing listings", file=open(os.devnull, 'w'))

    for batch in batches:
        results = []
        for v in batch:
            vehicle = parse_vehicle_info(driver, v["url"])
            if vehicle:
                vehicle["run_id"] = run_id
                results.append(vehicle)
            logger.info(str(pbar))
            pbar.update(1)

        try:
            output_path = output_partfile_template.format(idx=global_idx)
            logger.debug(f"Saving progress into batch `{output_path}` ...")
            df = pd.DataFrame(results)
            df.to_csv(output_path, index=False)
            logger.debug(f"Batch saving successful.")
        except Exception as err:
            logger.error(f"Error occurred while saving batch: {err}")

        global_idx += 1

    pbar.close()
    driver.quit()
