from celery import chain, group
from dependency_injector.wiring import Provide, inject
from more_itertools import first

from core.services.brand_service import BrandService
from core.services.listing_service import ListingService
from core.services.vehicle_service import VehicleService
from infra.containers import Container
from infra.factory.logger import LoggerFactory
from infra.scraping.listing_scraper import ListingScraper
from infra.scraping.vehicle_scraper import VehicleScraper
from worker.main import celery_app


@celery_app.task(bind=True)
@inject
def process_listings_for_brand(
    self,
    brand_slug: str,
    run_id: str = None,
    listing_scraper: ListingScraper = Provide[Container.listing_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
    brand_service: BrandService = Provide[Container.brand_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    task_name = str(self.name).strip()
    logger = logger_factory.create(f"{task_name}.{brand_slug}")

    brand = brand_service.get_brand_by_slug(brand_slug)
    if brand is None:
        log_msg = f"Brand with slug={brand_slug} not found."
        logger.error(log_msg)
        raise ValueError(log_msg)

    if run_id is None:
        run_id = str(self.request.id).strip()

    logger.info(f"Processing brand: {brand.slug} (run_id={run_id})")

    count = 0
    for listing in listing_scraper.run(brand):
        listing.run_id = run_id
        logger.debug(f"Writing listing.listing_id={listing.id} into the listings table...")
        listing_service.insert_listing(listing)
        count += 1

    logger.info(f"Completed processing {count} listings for brand {brand.name}")
    return {"brand": brand.name, "count": count, "run_id": run_id}


@celery_app.task(bind=True)
@inject
def spawn_listing_tasks(
    self,
    brand_service: BrandService = Provide[Container.brand_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    run_id = str(self.request.id).strip()
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    logger.info(f"Coordinator task started with run_id={run_id}")
    logger.info("Loading brands from seed file")
    brands = brand_service.load_brands()
    logger.info(f"Loaded {len(brands)} brands")

    job = group(
        process_listings_for_brand.s(
            brand_slug=brand.slug,
            run_id=run_id,
        )
        for brand in brands
    )

    logger.info(f"Spawning {len(brands)} brand listings processing tasks")
    result = job.apply_async()

    return {
        "run_id": run_id,
        "total_brands": len(brands),
        "group_id": result.id,
        "status": "spawned",
    }


@celery_app.task(bind=True)
@inject
def process_listing(
    self,
    listing_id: str,
    vehicle_scraper: VehicleScraper = Provide[Container.vehicle_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
    vehicle_service: VehicleService = Provide[Container.vehicle_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    logger.info(f"Processing listing_id={listing_id}")
    vehicle = vehicle_service.get_vehicle(listing_id)
    if vehicle:
        logger.debug(f"Vehicle for listing_id={listing_id} already exists. Skipping processing.")
        return {"listing_id": listing_id, "status": "skipped"}

    listing = listing_service.find_latest(listing_id)

    if listing is None:
        logger.error(f"Listing with id={listing_id} not found.")
        return {"listing_id": listing_id, "status": "not_found"}

    vehicles = list(vehicle_scraper.run([listing]))
    if vehicles:
        vehicle = vehicles[0]
        logger.debug(f"Writing vehicle.listing_id={vehicle.id} into the vehicles table...")
        vehicle_service.insert_vehicle(vehicle)
        return {"listing_id": listing.id, "status": "success"}
    else:
        logger.warning(f"No vehicle data extracted for listing.id={listing.id}")
        return {"listing_id": listing.id, "status": "empty_result"}


@celery_app.task(bind=True)
@inject
def spawn_vehicle_tasks_for_run(
    self,
    run_id: str,
    listing_service: ListingService = Provide[Container.listing_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    logger.info(f"Retrieving listings for run_id={run_id}.")
    listings = listing_service.repo.find_without_vehicle_by_run_id(run_id)
    logger.info(f"Found {len(listings)} listings for run_id={run_id}.")

    if not listings:
        logger.info("No listings found to process.")
        return {"status": "empty_input", "count": 0, "run_id": run_id}

    job = group(process_listing.s(listing_id=listing.id) for listing in listings)

    logger.info(f"Spawning {len(listings)} vehicle processing tasks")
    result = job.apply_async()

    return {
        "run_id": run_id,
        "total_listings": len(listings),
        "group_id": result.id,
        "status": "spawned",
    }


@celery_app.task(bind=True)
@inject
def spawn_vehicle_tasks(
    self,
    prev_result: dict | None = None,
    listing_service: ListingService = Provide[Container.listing_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    # run_id should be obtained from previous task result if available
    run_id = None
    if prev_result and isinstance(prev_result, dict):
        run_id = prev_result.get("run_id")
        logger.info(f"Received run_id={run_id} from previous task.")

    # fallback, query for the latest run
    if not run_id:
        logger.info("No run_id from previous task. Querying for latest run.")
        listings = listing_service.search_last_ingested_listings()
        if listings:
            run_id = first(listings).run_id
            logger.info(f"Found last ingested run_id={run_id}.")
        else:
            logger.warning("No listings found to process.")
            return {"status": "empty_input", "count": 0}
    else:
        logger.info(f"Retrieving listings for run_id={run_id}.")
        listings = listing_service.repo.find_without_vehicle_by_run_id(run_id)

    logger.info(f"Found {len(listings)} listings for run_id={run_id}.")

    if not listings:
        logger.info("No listings found to process.")
        return {"status": "empty_input", "count": 0, "run_id": run_id}

    job = group(process_listing.s(listing_id=listing.id) for listing in listings)

    logger.info(f"Spawning {len(listings)} vehicle processing tasks")
    result = job.apply_async()

    return {
        "run_id": run_id,
        "total_listings": len(listings),
        "group_id": result.id,
        "status": "spawned",
    }


@celery_app.task
def pipeline():
    workflow = chain(spawn_listing_tasks.s(), spawn_vehicle_tasks.s())
    return workflow.apply_async()
