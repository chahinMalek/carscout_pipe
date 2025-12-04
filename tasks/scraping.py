from dependency_injector.wiring import inject, Provide

from more_itertools import first

from app.celery_app import celery_app
from core.entities.brand import Brand
from core.services.listing_service import ListingService
from core.services.vehicle_service import VehicleService
from infra.containers import Container
from infra.factory.logger import LoggerFactory
from infra.scraping.listing_scraper import ListingScraper
from infra.scraping.vehicle_scraper import VehicleScraper


@celery_app.task(bind=True)
@inject
def process_listings(
    self,
    listing_scraper: ListingScraper = Provide[Container.listing_scraper],
    service: ListingService = Provide[Container.listing_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    run_id = str(self.request.id).strip()
    task_name = str(self.name).strip()
    logger = logger_factory.create(task_name)

    brands = [
        Brand(id="3", name="Alfa Romeo", slug="alfa-romeo"),
        Brand(id="7", name="Audi", slug="audi"),
        Brand(id="11", name="BMW", slug="bmw"),
    ]

    for brand in brands:
        for listing in listing_scraper.run(brand):
            listing.run_id = run_id
            logger.debug(f"Writing listing.listing_id={listing.id} into the listings table...")
            service.insert_listing(listing)


@celery_app.task(bind=True)
@inject
def process_vehicles(
    self,
    vehicle_scraper: VehicleScraper = Provide[Container.listing_scraper],
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

    for listing in listings:
        vehicle = vehicle_scraper.run(listing)
        logger.debug(f"Writing vehicle.listing_id={listing.id} into the vehicles table...")
        vehicle_service.insert_vehicle(vehicle)
