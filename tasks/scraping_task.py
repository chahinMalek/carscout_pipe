from dependency_injector.wiring import inject, Provide

from core.entities.brand import Brand
from core.services.listing_service import ListingService
from app.celery_app import celery_app
from infra.containers import Container
from infra.factory.logger import LoggerFactory
from infra.scraping.listing_scraper import ListingScraper


@celery_app.task(bind=True)
@inject
def process_listings(
    self,
    scraper: ListingScraper = Provide[Container.listing_scraper],
    service: ListingService = Provide[Container.listing_service],
    logger_factory: LoggerFactory = Provide[Container.logger_factory],
):
    """
    Celery task:
      1. Uses ListingScraper to fetch raw listings.
      2. Uses ListingService to validate, transform and persist them.
    """
    run_id = str(self.request.id).strip()
    # task_name = str(self.name).strip()

    logger = logger_factory.create("task.process_listings")
    brands = [
        Brand(id="3", name="Alfa Romeo", slug="alfa-romeo"),
        Brand(id="7", name="Audi", slug="audi"),
        Brand(id="11", name="BMW", slug="bmw"),
    ]
    for brand in brands:
        for listing in scraper.run(brand):
            listing.run_id = run_id
            logger.debug(f"Writing listing.id={listing.id} into the listings table...")
            service.insert_listing(listing)
