import uuid
from dataclasses import asdict
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from infra.containers import Container


def on_pipeline_failure(context):
    """
    Callback triggered when the DAG run fails.
    Ensures the 'runs' table reflects the failure and records the error message.
    """
    container = Container.create_and_patch()
    dag_run = context.get("dag_run")
    if not dag_run:
        logger = container.logger_factory().create("airflow.on_pipeline_failure")
        logger.error("DAG run not found, skipping...")
        return

    run_id = context["ti"].xcom_pull(task_ids="prepare_run", key="return_value")
    if isinstance(run_id, list) and len(run_id) > 0:
        run_id = run_id[0]

    if not run_id:
        run_id = dag_run.conf.get("run_id")

    if not run_id:
        logger = container.logger_factory().create("airflow.on_pipeline_failure")
        logger.error("Run ID not found, skipping...")
        return

    logger = container.logger_factory().create(
        "airflow.on_pipeline_failure",
        context={"run_id": str(run_id)},
    )
    run_service = container.run_service()

    # identify which task failed
    failed_ti = context.get("task_instance")
    task_id = failed_ti.task_id if failed_ti else "unknown"
    exception = context.get("exception")
    map_index = failed_ti.map_index if failed_ti else None

    err_msg = (
        f"Pipeline failed at task: {task_id} (index: {map_index})."
        if map_index is not None
        else f"Pipeline failed at task: {task_id}. Error: {str(exception)}"
        if exception
        else f"Pipeline failed at task: {task_id}."
    )
    logger.error(err_msg)
    logger.info("Marking run as failed.")
    run_service.fail_run(str(run_id), err_msg)
    logger.info("Run marked as failed.")


def on_pipeline_success(context):
    """
    Callback triggered when the entire DAG completes successfully.
    """
    container = Container.create_and_patch()
    dag_run = context.get("dag_run")
    if not dag_run:
        logger = container.logger_factory().create("airflow.on_pipeline_success")
        logger.error("DAG run not found, skipping...")
        return

    run_id = context["ti"].xcom_pull(task_ids="prepare_run", key="return_value")
    if isinstance(run_id, list) and len(run_id) > 0:
        run_id = run_id[0]

    if not run_id:
        run_id = dag_run.conf.get("run_id")

    if not run_id:
        logger = container.logger_factory().create("airflow.on_pipeline_success")
        logger.error("Run ID not found, skipping...")
        return

    logger = container.logger_factory().create(
        "airflow.on_pipeline_success",
        context={"run_id": run_id},
    )
    run_service = container.run_service()

    # Ensure run_id is a string before passing it to internal services
    logger.info("Marking run as completed.")
    run_service.complete_run(str(run_id))
    logger.info("Pipeline completed successfully.")


@dag(
    dag_id="carscout_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2},
    on_failure_callback=on_pipeline_failure,
    on_success_callback=on_pipeline_success,
)
def carscout_pipeline():
    @task
    def prepare_run(**context):
        """
        Generates or reuses run_id and returns it. Helps track the pipeline run.
        """
        import json

        run_id = context.get("dag_run").conf.get("run_id") if context.get("dag_run") else None
        if run_id is None:
            run_id = str(uuid.uuid4())

        # init container, services and database
        container = Container.create_and_patch()
        container.init_db()
        run_service = container.run_service()

        logger = container.logger_factory().create(
            "airflow.prepare_run",
            context={"run_id": run_id},
        )
        logger.info(f"Starting run: {run_id}")
        logger.info(f"Using configuration: {json.dumps(container.config(), indent=2)}")

        run_service.start_run(run_id)

        return run_id

    @task
    def get_brands():
        """
        Loads brands from seed file and returns them as a list of dicts for mapping.
        """
        container = Container.create_and_patch()
        brand_service = container.brand_service()
        brand_service.read_brands()
        brands = brand_service.load_brands()
        # convert dataclasses to dicts for xcom serialization
        return [asdict(b) for b in brands]

    @task(
        max_active_tis_per_dag=1,
        execution_timeout=timedelta(minutes=30),
    )
    def process_listings(brand_dict: dict, task_run_id: str):
        """
        Processes listings for a single brand.
        """

        from core.entities.brand import Brand

        brand = Brand(**brand_dict)

        # init container and services
        container = Container.create_and_patch()
        logger = container.logger_factory().create(
            f"airflow.listings.{brand.slug}",
            context={"run_id": task_run_id, "brand": brand.slug},
        )
        listing_scraper = container.listing_scraper()
        listing_service = container.listing_service()
        run_service = container.run_service()

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
                    run_service.update_metrics(task_run_id, num_errors=1)

            logger.info(f"Completed {brand.name}: {success_listings} listings")
            run_service.update_metrics(task_run_id, num_listings=success_listings)

        except Exception as err:
            logger.error(f"Failed to process {brand.slug}: {err}", exc_info=True)
            # Re-raise so the failure callback can catch it
            run_service.update_metrics(task_run_id, num_errors=1)
            raise
            # Note: we can also skip throwing an exception and let the pipeline continue

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
            raise AirflowSkipException("No task_run_id found, skipping vehicle processing.")

        # init container and services
        container = Container.create_and_patch()
        logger = container.logger_factory().create(
            "airflow.process_vehicles",
            context={"run_id": task_run_id},
        )
        vehicle_scraper = container.vehicle_scraper()
        listing_service = container.listing_service()
        vehicle_service = container.vehicle_service()
        run_service = container.run_service()

        # retrieve listings without vehicles for the given task_run_id
        logger.info(f"Retrieving listings for task_run_id={task_run_id}")
        listings = listing_service.repo.find_without_vehicle_by_run_id(task_run_id)
        logger.info(f"Found {len(listings)} listings for task_run_id={task_run_id}")

        if not listings:
            msg = "No listings to process."
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
                run_service.update_metrics(task_run_id, num_errors=1)

        # update run metrics
        run_service.update_metrics(task_run_id, num_vehicles=success, num_errors=failed)

        # push results to xcom for subsequent tasks
        result = {
            "run_id": task_run_id,
            "total_listings": total,
            "processed_listings": success + failed,
            "success_listings": success,
            "failed_listings": failed,
        }
        return result

    @task(
        trigger_rule="all_done",  # ensures the task runs even if some brands failed
    )
    def summarize_run(vehicle_results: dict):
        container = Container.create_and_patch()
        logger = container.logger_factory().create("airflow.summarize")

        logger.info("--- RUN SUMMARY ---")
        if not vehicle_results:
            logger.warning(
                "No vehicle results to summarize (upstream might have been skipped or failed)."
            )
            return

        run_id = vehicle_results.get("run_id", "unknown")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Total Number of Listings: {vehicle_results.get('total_listings', 0)}")
        logger.info(f"Total Listings Processed: {vehicle_results.get('processed_listings', 0)}")
        logger.info(f"Total Vehicles Scraped: {vehicle_results.get('success_listings', 0)}")
        logger.info(f"Total Vehicles Failed: {vehicle_results.get('failed_listings', 0)}")

    # orchestration flow
    task_run_id = prepare_run()
    brands = get_brands()

    # map listings tasks over brands
    listings_stats = process_listings.partial(task_run_id=task_run_id).expand(brand_dict=brands)

    # process vehicles after listings are done
    vehicle_results = process_vehicles(task_run_id=task_run_id, listing_results=listings_stats)

    # summarize run
    summarize_run(vehicle_results)


# instantiate the DAG
carscout_pipeline()
