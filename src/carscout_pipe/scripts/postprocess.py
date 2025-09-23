import datetime
import time
import uuid
from datetime import timedelta

from src.carscout_pipe.core.api_requests.vehicles import extract_vehicle_details, init_request_session
from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.scraping.webdriver import init_driver
from src.carscout_pipe.infra.db.service import db_service
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)

RUN_ID = str(uuid.uuid4())
LOOKBACK_DAYS = 5
REINIT_SESSION_EVERY = 500
MIN_REQUEST_DELAY_SECS = 0.5
MAX_REQUEST_DELAY_SECS = 2


def postprocess_vehicles_with_null_attributes():
    """Postprocess vehicles that have null brand or model values by re-scraping and updating them."""
    scrape_start = time.time()
    driver = None
    errors = False

    today = datetime.datetime.now()
    keep_after = today - timedelta(days=LOOKBACK_DAYS)

    try:
        logger.info(f"Starting postprocessing run: {RUN_ID}")
        logger.info("Identifying vehicles with null attributes (brand or model)...")
        
        # Get vehicles with null brand or model
        vehicles_with_nulls = db_service.get_vehicles_with_null_attributes(keep_after=keep_after)
        total_vehicles = len(vehicles_with_nulls)
        
        if total_vehicles == 0:
            logger.info("No vehicles with null attributes found. Nothing to postprocess.")
            return

        logger.info(f"Found {total_vehicles} vehicles with null attributes. Starting rescraping...")
        driver = init_driver()
        session = init_request_session(driver)
        
        updated_count = 0
        failed_count = 0
        
        for i, vehicle_data in enumerate(vehicles_with_nulls, start=1):
            if i % REINIT_SESSION_EVERY == 0:
                session = init_request_session(driver)

            try:
                logger.info(f"Processing vehicle {i}/{total_vehicles}: {vehicle_data['url']}")
                
                # Create a Listing object from the vehicle data
                listing = Listing(
                    listing_id=vehicle_data['listing_id'],
                    url=vehicle_data['url'],
                    title=vehicle_data['title'],
                    price=vehicle_data['price']
                )
                
                # Extract updated vehicle details
                updated_vehicle = extract_vehicle_details(
                    session=session,
                    listing=listing,
                    min_delay=MIN_REQUEST_DELAY_SECS,
                    max_delay=MIN_REQUEST_DELAY_SECS,
                )
                
                if updated_vehicle:
                    # Update the vehicle in the database
                    success = db_service.update_vehicle(vehicle_data['listing_id'], updated_vehicle)
                    if success:
                        updated_count += 1
                        logger.info(f"Successfully updated vehicle {i}/{total_vehicles}: {vehicle_data['listing_id']}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to update vehicle in database: {vehicle_data['listing_id']}")
                        errors = True
                else:
                    failed_count += 1
                    logger.warning(f"Failed to extract updated vehicle details: {vehicle_data['url']}")
                    errors = True
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing vehicle {vehicle_data['listing_id']}: {e}")
                errors = True

        logger.info(f"Postprocessing completed. Updated: {updated_count}, Failed: {failed_count}")
        
    except Exception as e:
        logger.error(f"Unexpected error during postprocessing run '{RUN_ID}': {e}")
        errors = True
        
    finally:
        if driver:
            driver.quit()
        log_msg = f"Finished postprocessing run '{RUN_ID}'."
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

    logger.info("Starting vehicle attributes postprocessing...")
    postprocess_vehicles_with_null_attributes()

    logger.info("Postprocessing completed.")


if __name__ == '__main__':
    main()
