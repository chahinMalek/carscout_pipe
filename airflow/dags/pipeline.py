import uuid
from datetime import datetime

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator
from infra.bootstrap import bootstrap_container


def process_listings(**context):
    ti = context["ti"]

    # Generate or reuse run_id
    run_id = context.get("dag_run").conf.get("run_id") if context.get("dag_run") else None
    if run_id is None:
        run_id = str(uuid.uuid4())

    ti.xcom_push(key="run_id", value=run_id)

    container = bootstrap_container()
    logger = container.logger_factory().create("airflow.process_listings")

    brand_service = container.brand_service()
    brand_service.read_brands()
    listing_scraper = container.listing_scraper()
    listing_service = container.listing_service()

    logger.info("Loading brands from seed file")
    brands = brand_service.load_brands()
    logger.info("Loaded %s brands", len(brands))

    failed_brands = []
    success_listings = 0
    failed_listings = 0

    for i, brand in enumerate(brands, start=1):
        logger.info("Processing brand %s/%s: %s", i, len(brands), brand.slug)

        try:
            count = 0
            for listing in listing_scraper.run(brand):
                try:
                    listing.run_id = run_id
                    listing_service.insert_listing(listing)
                    count += 1
                except Exception:
                    logger.error(
                        "Failed to insert listing.id=%s",
                        listing.id,
                        exc_info=True,
                    )
                    failed_listings += 1

            success_listings += count
            logger.info("Completed %s: %s listings", brand.name, count)

        except Exception as e:
            logger.error("Failed to process brand %s", brand.slug, exc_info=True)
            failed_brands.append({"brand": brand.slug, "error": str(e)})

    result = {
        "run_id": run_id,
        "total_brands": len(brands),
        "success_brands": len(brands) - len(failed_brands),
        "failed_brands": failed_brands,
        "success_listings": success_listings,
        "failed_listings": failed_listings,
    }

    ti.xcom_push(key="listings_result", value=result)
    return result


def process_vehicles(**context):
    """
    Refactor of Celery `process_vehicles` task
    """
    ti = context["ti"]

    run_id = ti.xcom_pull(task_ids="process_listings", key="run_id")
    if not run_id:
        raise AirflowSkipException("No run_id found, skipping vehicle processing")

    container = bootstrap_container()
    logger = container.logger_factory().create("airflow.process_vehicles")

    vehicle_scraper = container.vehicle_scraper()
    listing_service = container.listing_service()
    vehicle_service = container.vehicle_service()

    logger.info("Retrieving listings for run_id=%s", run_id)
    listings = listing_service.repo.find_without_vehicle_by_run_id(run_id)
    logger.info("Found %s listings for run_id=%s", len(listings), run_id)

    if not listings:
        logger.info("No listings to process")
        raise AirflowSkipException("No listings without vehicles")

    total = len(listings)
    success = 0
    failed = 0

    for vehicle in vehicle_scraper.run(listings):
        try:
            if vehicle:
                vehicle_service.insert_vehicle(vehicle)
                success += 1
            else:
                failed += 1
        except Exception:
            logger.error(
                "Failed to insert vehicle.listing_id=%s",
                vehicle.id if vehicle else None,
                exc_info=True,
            )
            failed += 1

    result = {
        "run_id": run_id,
        "total_listings": total,
        "processed_listings": success + failed,
        "success_listings": success,
        "failed_listings": failed,
    }

    ti.xcom_push(key="vehicles_result", value=result)
    return result


with DAG(
    dag_id="vehicle_scraping_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,  # 🔥 prevents overlapping runs
    concurrency=1,  # 🔥 prevents parallel execution
    default_args={
        "retries": 2,
    },
    tags=["scraping", "vehicles"],
) as dag:
    listings_task = PythonOperator(
        task_id="process_listings",
        python_callable=process_listings,
        provide_context=True,
    )

    vehicles_task = PythonOperator(
        task_id="process_vehicles",
        python_callable=process_vehicles,
        provide_context=True,
    )

    listings_task >> vehicles_task
