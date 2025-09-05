import os
import random
import sys
import uuid
from datetime import datetime
from logging import DEBUG

import pandas as pd
from scrapy import Selector
from selenium.common.exceptions import TimeoutException, WebDriverException
from tqdm import tqdm

from carscout_pipe.exceptions import OlxPageNotFound
from carscout_pipe.utils.logging import get_logger
from carscout_pipe.utils.scraping import get_next_page, parse_vehicle_info
from carscout_pipe.utils.webdriver import init_driver, get_page_source

logger = get_logger(__name__, log_level=DEBUG)

if __name__ == '__main__':

    # script-level parameters
    # todo: replace with fetching brands from the db
    brands_path = "./data/brands.csv"
    request_min_delay_seconds = 1
    request_max_delay_seconds = 5
    wait_time_seconds = 8

    # script-level constants
    driver = None
    url_template = (
        "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
        "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
    )
    run_id = str(uuid.uuid4())
    output_dir = f"./data/output/{run_id}/"
    filename_template = "part_{idx:08}.csv"
    output_partfile_template = os.path.join(output_dir, filename_template)
    global_idx = 0

    logger.debug("Starting process with parameters:")
    logger.debug(f"{brands_path=}")
    logger.debug(f"{request_min_delay_seconds=}")
    logger.debug(f"{request_max_delay_seconds=}")
    logger.debug(f"{wait_time_seconds=}")
    logger.debug(f"{run_id=}")

    logger.debug("Initializing output directory ...")
    os.makedirs(output_dir, exist_ok=True)

    logger.debug("Reading brands ...")
    brands = pd.read_csv(brands_path).to_dict(orient="records")

    try:
        try:
            logger.debug("Initializing WebDriver")
            driver = init_driver()
        except (TimeoutError, WebDriverException) as e:
            logger.error("Failed to initialize WebDriver. Exiting...")
            sys.exit(1)

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
                            logger.error(f"Error retrieving vehicle page {listing_url}: Timed out.")
                        except OlxPageNotFound as err:
                            logger.error(f"Error retrieving vehicle page {listing_url}: Not found.")
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
