import os

from dependency_injector import containers, providers

from core.services.listing_service import ListingService
from core.services.vehicle_service import VehicleService
from infra.db.models.base import Base
from infra.db.repositories.listings import SqlAlchemyListingRepository
from infra.db.repositories.vehicles import SqlAlchemyVehicleRepository
from infra.db.service import DatabaseService
from infra.factory.clients.http import HttpClientFactory, ClientType
from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory
from infra.resources.brands import read_brands
from infra.scraping.listing_scraper import ListingScraper


class Container(containers.DeclarativeContainer):

    environment = os.environ.get("ENVIRONMENT") or "development"

    config = providers.Configuration()
    config.environment.from_value(environment)

    script_path = os.path.dirname(__file__)
    config.from_yaml(os.path.join(script_path, "config/config.yml"))

    # database
    db_service = providers.Singleton(
        DatabaseService,
        connection_string=config.db.url,
        echo=config.db.echo,
    )

    # resources
    init_db = providers.Resource(
        lambda db: db.create_all_tables(Base),
        db=db_service,
    )
    read_brands = providers.Resource(
        read_brands,
        path=config.resources.brands,
    )

    # repositories
    listing_repository = providers.Singleton(
        SqlAlchemyListingRepository,
        db_service=db_service,
    )
    vehicle_repository = providers.Singleton(
        SqlAlchemyVehicleRepository,
        db_service=db_service,
    )

    # services
    listing_service = providers.Singleton(
        ListingService,
        repo=listing_repository,
    )
    vehicle_service = providers.Singleton(
        VehicleService,
        repo=vehicle_repository,
    )

    # factories
    logger_factory = providers.Singleton(
        LoggerFactory,
        log_level=config.logging.log_level.as_int(),
        format=config.logging.format,
    )
    webdriver_factory = providers.Singleton(
        WebdriverFactory,
        chrome_options=config.webdriver.chrome_options,
        use_stealth=config.webdriver.use_stealth,
        logger_factory=logger_factory,
        timeout_seconds=config.webdriver.timeout_seconds,
    )
    http_client_factory = providers.Singleton(
        HttpClientFactory,
        url=config.http.url,
        headers=config.http.headers,
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        client_type=config.http.client_type.as_(lambda x: ClientType(x)),
    )

    # scrapers
    listing_scraper = providers.Singleton(
        ListingScraper,
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        http_client_factory=http_client_factory,
        min_req_delay=config.scrapers.listing_scraper.min_req_delay,
        max_req_delay=config.scrapers.listing_scraper.max_req_delay,
        timeout=config.scrapers.listing_scraper.timeout,
    )
