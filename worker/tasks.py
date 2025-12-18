import uuid

from celery import chain
from dependency_injector.wiring import Provide, inject

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
def process_listings(
    self,
    run_id: str | None = None,
    brand_service: BrandService = Provide[Container.brand_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
    listing_scraper: ListingScraper = Provide[Container.listing_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
):
    if run_id is None:
        run_id = str(uuid.uuid4())

    task_name = str(self.name).strip()
    task_id = str(self.request.id).strip()
    logger = logger_factory.create(f"{task_name}[{task_id}]")

    logger.info("Loading brands from seed file")
    brands = brand_service.load_brands()
    logger.info(f"Loaded {len(brands)} brands")

    failed_brands = []
    success_listings = 0
    failed_listings = 0

    for i, brand in enumerate(brands, start=1):
        logger.info(f"Processing brand {i}/{len(brands)}: {brand.slug}")

        try:
            count = 0
            for listing in listing_scraper.run(brand):
                try:
                    listing.run_id = run_id
                    logger.debug(f"Writing listing.listing_id={listing.id}")
                    listing_service.insert_listing(listing)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to insert listing.id={listing.id}: {e}", exc_info=True)
                    failed_listings += 1

            success_listings += count
            logger.info(f"Completed {brand.name}: {count} listings")

            self.update_state(
                state="PROGRESS",
                meta={
                    "total_brands": len(brands),
                    "current_brand": brand.slug,
                    "processed_brands": i,
                    "failed_brands": len(failed_brands),
                    "success_listings": success_listings,
                    "failed_listings": failed_listings,
                },
            )

        except Exception as e:
            # log the error and continue with the next brand
            logger.error(f"Failed to process {brand.slug}: {e}", exc_info=True)
            failed_brands.append({"brand": brand.slug, "error": str(e)})

    return {
        "run_id": run_id,
        "task_id": task_id,
        "task_name": task_name,
        "status": "finished",
        "total_brands": len(brands),
        "success_brands": len(brands) - len(failed_brands),
        "failed_brands": failed_brands,
        "success_listings": success_listings,
        "failed_listings": failed_listings,
    }


@celery_app.task(bind=True)
@inject
def process_vehicles(
    self,
    run_id: str | None = None,
    vehicle_scraper: VehicleScraper = Provide[Container.vehicle_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
    vehicle_service: VehicleService = Provide[Container.vehicle_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    if run_id is None:
        run_id = str(uuid.uuid4())

    task_name = str(self.name).strip()
    task_id = str(self.request.id).strip()
    logger = logger_factory.create(f"{task_name}[{task_id}]")

    logger.info(f"Retrieving listings for run_id={run_id}.")
    listings = listing_service.repo.find_without_vehicle_by_run_id(run_id)
    logger.info(f"Found {len(listings)} listings for run_id={run_id}.")

    if not listings:
        logger.info(f"No listings found to process with run_id={run_id}.")
        return {
            "run_id": run_id,
            "task_id": task_id,
            "task_name": task_name,
            "status": "empty_input",
        }

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
        except Exception as e:
            logger.error(f"Failed to insert vehicle.listing_id={vehicle.id}: {e}", exc_info=True)
            failed += 1

        if (success + failed) % 100 == 0:
            self.update_state(
                state="PROGRESS",
                meta={
                    "total_listings": total,
                    "processed_listings": success + failed,
                    "success_listings": success,
                    "failed_listings": failed,
                },
            )

    return {
        "run_id": run_id,
        "task_id": task_id,
        "task_name": task_name,
        "status": "finished",
        "total_listings": total,
        "processed_listings": success + failed,
        "success_listings": success,
        "failed_listings": failed,
    }


@celery_app.task(bind=True)
def pipeline(self):
    run_id = str(self.request.id).strip()
    workflow = chain(process_listings.s(run_id=run_id), process_vehicles.si(run_id=run_id))
    return workflow.apply_async()
