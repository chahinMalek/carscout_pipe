import time
import uuid
from datetime import timedelta
from typing import List

import pandas as pd

from src.carscout_pipe.core.api_requests.vehicles import extract_vehicle_details, init_request_session
from src.carscout_pipe.core.data_models.brands import Brand
from src.carscout_pipe.core.scraping.listings import scrape_listings
from src.carscout_pipe.core.scraping.webdriver import init_driver
from src.carscout_pipe.infra.db.service import db_service
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)

BRANDS_CSV_PATH = "data/seeds/brands.csv"
RUN_ID = str(uuid.uuid4())
REINIT_SESSION_EVERY = 500
MIN_REQUEST_DELAY_SECS = 0.5
MAX_REQUEST_DELAY_SECS = 2


def load_brands() -> List[Brand]:
    """Load brands from CSV file."""
    df = pd.read_csv(BRANDS_CSV_PATH)
    return [Brand(**row) for _, row in df.iterrows()]


def extract_listings():
    scrape_start = time.time()
    driver = None
    errors = False

    try:
        logger.info(f"Loading brands from seed file...")
        brands = load_brands()
        num_brands = len(brands)

        logger.info(f"Starting scraping run: {RUN_ID}")
        driver = init_driver()

        for brand_num, brand in enumerate(brands, start=1):
            logger.info(f"Scraping listings for brand: '{brand.name}' ({brand_num}/{num_brands}) ...")
            try:
                listings_generator = scrape_listings(driver, brand)
                for listings in listings_generator:
                    num_inserted = db_service.store_listings(listings, run_id=RUN_ID)
                    logger.info(f"Found {num_inserted} listings for brand: '{brand.name}' ({brand_num}/{num_brands}) ...")
            except Exception as e:
                logger.error(f"Error scraping brand '{brand.name}': {e}")
                errors = True

    except Exception as e:
        logger.error(f"Unexpected error during scraping run '{RUN_ID}': {e}")

    finally:
        if driver:
            driver.quit()
        log_msg = f"Finished listing extraction run '{RUN_ID}'."
        elapsed_time = time.time() - scrape_start
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        log_msg += f"\nTotal runtime: {elapsed_str}."
        logger.info(log_msg)
        if errors:
            err_msg = "Some errors occurred during this process. Please check the logs for details."
            logger.info(err_msg)


def extract_vehicles():
    scrape_start = time.time()
    driver = None
    errors = False

    try:
        logger.info(f"Identifying new listings...")
        new_listings = db_service.get_listings_without_vehicles(RUN_ID)
        total_listings = len(new_listings)
        
        if total_listings == 0:
            logger.info("No new listings found. Skipping vehicle information extraction.")
            return

        logger.info(f"Found {total_listings} new listings. Resuming vehicle information extraction.")
        driver = init_driver()
        session = init_request_session(driver)
        
        for i, listing in enumerate(new_listings, start=1):
            if i % REINIT_SESSION_EVERY == 0:
                session = init_request_session(driver)
            try:
                logger.info(f"Extracting vehicle details for listing {i}/{total_listings}: {listing.url}")
                vehicle = extract_vehicle_details(
                    session=session,
                    listing=listing,
                    min_delay=MIN_REQUEST_DELAY_SECS,
                    max_delay=MAX_REQUEST_DELAY_SECS,
                )
                if vehicle:
                    success = db_service.store_vehicle(vehicle, run_id=RUN_ID)
                    if not success:
                        logger.error(f"Failed to store vehicle details for listing: {listing.url}")
                        errors = True
                else:
                    logger.warning(f"Failed to extract vehicle details for listing: {listing.url}")
                    errors = True
                    
            except Exception as e:
                logger.error(f"Error processing listing {listing.url}: {e}")
                errors = True

        logger.info(f"Vehicle extraction completed.")
        
    except Exception as e:
        logger.error(f"Unexpected error during vehicle information extraction: {e}")
        errors = True
        
    finally:
        if driver:
            driver.quit()
        log_msg = f"Finished extracting vehicle information run '{RUN_ID}'."
        elapsed_time = time.time() - scrape_start
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        log_msg += f"\nTotal runtime: {elapsed_str}."
        logger.info(log_msg)
        if errors:
            err_msg = "Some errors occurred during this process. Please check the logs for details."
            logger.info(err_msg)


def main() -> None:
    logger.info("Initializing database...")
    db_service.initialize_database()

    logger.info(f"Step 1/2: Start listings extraction...")
    extract_listings()

    logger.info(f"Step 2/2: Start vehicle information extraction...")
    extract_vehicles()

    logger.info("Process completed.")
    


if __name__ == '__main__':
    main()
