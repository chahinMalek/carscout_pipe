import uuid
from dataclasses import asdict
from datetime import datetime

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from infra.containers import Container


def prepare_run(**context):
    """Generates or reuses run_id and pushes it to XCom."""
    run_id = context.get("dag_run").conf.get("run_id") if context.get("dag_run") else None
    if run_id is None:
        run_id = str(uuid.uuid4())
    return run_id


def get_brands(**context):
    """Loads brands from seed file and returns them as a list of dicts for mapping."""
    container = Container.create_and_patch()
    brand_service = container.brand_service()
    brand_service.read_brands()
    brands = brand_service.load_brands()
    # Convert dataclasses to dicts for XCom serialization
    return [asdict(b) for b in brands]


def process_listings(brand_dict: dict, **context):
    """Processes listings for a single brand."""
    ti = context["ti"]

    # Get run_id from the prepare_run task
    run_id = ti.xcom_pull(task_ids="prepare_run")

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
                listing.run_id = run_id
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


def process_vehicles(**context):
    """
    Identifies listings for which vehicle information is missing.
    Requires a run_id to be provided.
    Processes all identified listings to scrape and store vehicle data.
    """

    ti = context["ti"]

    # try getting run_id from dag_run conf first (for manual/independent triggers)
    run_id = context.get("dag_run").conf.get("run_id") if context.get("dag_run") else None

    # fallback to xcom if not in conf
    if not run_id:
        run_id = ti.xcom_pull(task_ids="prepare_run")

    if not run_id:
        raise AirflowSkipException("No run_id found, skipping vehicle processing")

    # init container and services
    container = Container.create_and_patch()
    logger = container.logger_factory().create("airflow.process_vehicles")
    vehicle_scraper = container.vehicle_scraper()
    listing_service = container.listing_service()
    vehicle_service = container.vehicle_service()

    # retrieve listings without vehicles for the given run_id
    logger.info(f"Retrieving listings for run_id={run_id}")
    listings = listing_service.repo.find_without_vehicle_by_run_id(run_id)
    logger.info(f"Found {len(listings)} listings for run_id={run_id}")

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
                logger.debug(f"Writing vehicle.listing_id={vehicle.id} into the vehicles table...")
                vehicle_service.insert_vehicle(vehicle)
                success += 1
            else:
                failed += 1
        except Exception as err:
            logger.error(f"Failed to insert vehicle.listing_id={vehicle.id}: {err}", exc_info=True)
            failed += 1

    # push results to xcom for subsequent tasks
    result = {
        "run_id": run_id,
        "total_listings": total,
        "processed_listings": success + failed,
        "success_listings": success,
        "failed_listings": failed,
    }
    return result


with DAG(
    dag_id="carscout_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2},
    tags=["scraping", "vehicles"],
) as dag:
    prepare_run_task = PythonOperator(
        task_id="prepare_run",
        python_callable=prepare_run,
    )

    get_brands_task = PythonOperator(
        task_id="get_brands",
        python_callable=get_brands,
    )

    # uses dynamic task mapping for listings
    # max_active_tis_per_dag=1 ensures we process one brand at a time to avoid blocking
    listings_task = PythonOperator.partial(
        task_id="process_listings",
        python_callable=process_listings,
        max_active_tis_per_dag=1,
    ).expand(brand_dict=get_brands_task.output)

    vehicles_task = PythonOperator(
        task_id="process_vehicles",
        python_callable=process_vehicles,
    )

    prepare_run_task >> get_brands_task >> listings_task >> vehicles_task
