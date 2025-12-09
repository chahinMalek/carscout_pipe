from celery import chain
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
def process_listings(
    self,
    listing_scraper: ListingScraper = Provide[Container.listing_scraper],
    service: ListingService = Provide[Container.listing_service],
    brand_service: BrandService = Provide[Container.brand_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    run_id = str(self.request.id).strip()
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    logger.info("Loading brands from seed file")
    brands = brand_service.load_brands()
    logger.info(brands)
    logger.info(f"Loaded {len(brands)} brands")

    for brand in brands:
        for listing in listing_scraper.run(brand):
            listing.run_id = run_id
            logger.debug(f"Writing listing.listing_id={listing.id} into the listings table...")
            service.insert_listing(listing)


@celery_app.task(bind=True, ignore_result=False)
@inject
def process_vehicles(
    self,
    prev_result=None,  # Accept chained result but ignore it
    vehicle_scraper: VehicleScraper = Provide[Container.vehicle_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
    vehicle_service: VehicleService = Provide[Container.vehicle_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    logger.info("Attempting to retrieve last ingested listings.")
    listings = listing_service.search_last_ingested_listings()
    logger.info(f"Found {len(listings)} last ingested listings.")

    if not listings:
        return

    run_id = first(listings).run_id
    logger.info(f"Last ingested run_id={run_id}.")

    for vehicle in vehicle_scraper.run(listings):
        logger.debug(f"Writing vehicle.listing_id={vehicle.id} into the vehicles table...")
        vehicle_service.insert_vehicle(vehicle)


@celery_app.task
def pipeline():
    workflow = chain(process_listings.si(), process_vehicles.si())
    return workflow.apply_async()
