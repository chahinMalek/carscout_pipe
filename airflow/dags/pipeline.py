import uuid
from dataclasses import asdict
from datetime import datetime

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from infra.containers import Container


@dag(
    dag_id="carscout_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2},
    tags=["scraping", "vehicles"],
)
def carscout_pipeline():
    @task
    def prepare_run(**context):
        """
        generates or reuses run_id and returns it
        """
        run_id = context.get("dag_run").conf.get("run_id") if context.get("dag_run") else None
        if run_id is None:
            run_id = str(uuid.uuid4())
        return run_id

    @task
    def get_brands():
        """
        loads brands from seed file and returns them as a list of dicts for mapping
        """
        container = Container.create_and_patch()
        brand_service = container.brand_service()
        brand_service.read_brands()
        brands = brand_service.load_brands()
        # Convert dataclasses to dicts for XCom serialization
        return [asdict(b) for b in brands]

    @task(max_active_tis_per_dag=1)
    def process_listings(brand_dict: dict, task_run_id: str):
        """
        processes listings for a single brand
        """

        from core.entities.brand import Brand

        brand = Brand(**brand_dict)

        # init container and services
        container = Container.create_and_patch()
        logger = container.logger_factory().create(f"airflow.listings.{brand.slug}")
        listing_scraper = container.listing_scraper()
        listing_service = container.listing_service()

        logger.info(f"Processing brand: {brand.slug}")

        success_listings = 0
        failed_listings = 0

        try:
            for listing in listing_scraper.run(brand):
                try:
                    listing.run_id = task_run_id
                    logger.debug(f"Writing listing.listing_id={listing.id}")
                    listing_service.insert_listing(listing)
                    success_listings += 1
                except Exception as err:
                    logger.error(f"Failed to insert listing.id={listing.id}: {err}", exc_info=True)
                    failed_listings += 1

            logger.info(f"Completed {brand.name}: {success_listings} listings")
        except Exception as err:
            logger.error(f"Failed to process {brand.slug}: {err}", exc_info=True)
            raise

        return {
            "brand": brand.slug,
            "success_listings": success_listings,
            "failed_listings": failed_listings,
        }

    @task
    def process_vehicles(task_run_id: str, listing_results: list):
        """
        Identifies listings for which vehicle information is missing.
        Requires a run_id to be provided.
        Processes all identified listings to scrape and store vehicle data.
        """
        if not task_run_id:
            raise AirflowSkipException("No task_run_id found, skipping vehicle processing")

        # init container and services
        container = Container.create_and_patch()
        logger = container.logger_factory().create("airflow.process_vehicles")
        vehicle_scraper = container.vehicle_scraper()
        listing_service = container.listing_service()
        vehicle_service = container.vehicle_service()

        # retrieve listings without vehicles for the given task_run_id
        logger.info(f"Retrieving listings for task_run_id={task_run_id}")
        listings = listing_service.repo.find_without_vehicle_by_run_id(task_run_id)
        logger.info(f"Found {len(listings)} listings for task_run_id={task_run_id}")

        if not listings:
            msg = "No listings to process"
            logger.info(msg)
            raise AirflowSkipException(msg)

        # process each listing to scrape and store vehicle data
        total = len(listings)
        success = 0
        failed = 0

        for vehicle in vehicle_scraper.run(listings):
            try:
                if vehicle:
                    logger.debug(
                        f"Writing vehicle.listing_id={vehicle.id} into the vehicles table..."
                    )
                    vehicle_service.insert_vehicle(vehicle)
                    success += 1
                else:
                    failed += 1
            except Exception as err:
                logger.error(
                    f"Failed to insert vehicle.listing_id={vehicle.id}: {err}", exc_info=True
                )
                failed += 1

        # push results to xcom for subsequent tasks
        result = {
            "run_id": task_run_id,
            "total_listings": total,
            "processed_listings": success + failed,
            "success_listings": success,
            "failed_listings": failed,
        }
        return result

    # orchestration flow
    task_run_id = prepare_run()
    brands = get_brands()

    # map listings tasks over brands
    listings_stats = process_listings.partial(task_run_id=task_run_id).expand(brand_dict=brands)

    # process vehicles after listings are done
    process_vehicles(task_run_id=task_run_id, listing_results=listings_stats)


# instantiate the DAG
carscout_pipeline()
