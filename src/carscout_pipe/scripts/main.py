import time
import uuid
from datetime import timedelta
from typing import List

import pandas as pd

from src.carscout_pipe.core.data_models.brands import Brand
from src.carscout_pipe.core.scraping.listings import extract_listings
from src.carscout_pipe.core.scraping.webdriver import init_driver
from src.carscout_pipe.infra.db.service import db_service
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)

BRANDS_CSV_PATH = "data/seeds/brands.csv"
RUN_ID = str(uuid.uuid4())


def load_brands() -> List[Brand]:
    """Load brands from CSV file."""
    df = pd.read_csv(BRANDS_CSV_PATH)
    return [Brand(**row) for _, row in df.iterrows()]


def main() -> None:
    """Main scraping function with database integration."""
    errors = False
    scrape_start = time.time()

    try:
        logger.info("Initializing database...")
        db_service.initialize_database()

        logger.info(f"Loading brands from seed file...")
        brands = load_brands()
        num_brands = len(brands)

        logger.info(f"Starting scraping run: {RUN_ID}")
        brand_times = []
        
        for brand_num, brand in enumerate(brands, start=1):
            brand_start = time.time()
            
            logger.info(f"Scraping listings for brand: '{brand.name}' ({brand_num}/{num_brands}) ...")
            driver = init_driver()

            try:
                listings_generator = extract_listings(driver, brand)
                for listings in listings_generator:
                    logger.info(f"Scraped {len(listings)} listings for brand: '{brand.name}' ({brand_num}/{num_brands}) ...")
                    num_inserted = db_service.store_listings(listings, run_id=RUN_ID)
                    logger.info(f"Inserted {num_inserted} listings for brand: '{brand.name}' ({brand_num}/{num_brands}) ...")
            except Exception as e:
                logger.error(f"Error scraping brand '{brand.name}': {e}")
                errors = True
            finally:
                if driver:
                    driver.quit()
                    
            # Calculate and log timing information
            brand_time = time.time() - brand_start
            brand_times.append(brand_time)
            avg_time_per_brand = sum(brand_times) / len(brand_times)
            
            remaining_brands = num_brands - brand_num
            estimated_remaining_time = remaining_brands * avg_time_per_brand
            
            logger.info(
                f"Brand '{brand.name}' completed in {timedelta(seconds=int(brand_time))}. "
                f"Average time per brand: {timedelta(seconds=int(avg_time_per_brand))}. "
                f"Estimated time remaining: {timedelta(seconds=int(estimated_remaining_time))} "
                f"({brand_num}/{num_brands} brands completed)"
            )

    except Exception as e:
        logger.error(f"Unexpected error during scraping run '{RUN_ID}': {e}")
        errors = True
    finally:
        logger.info(
            f"Scraping run '{RUN_ID}' finished with errors."
            if errors else
            f"Scraping run '{RUN_ID}' finished successfully."
        )
        elapsed_time = time.time() - scrape_start
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))
        logger.info(f"Process finished after {elapsed_str}.")


if __name__ == '__main__':
    main()
