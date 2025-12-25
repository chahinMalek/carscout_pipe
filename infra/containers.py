import os

from dependency_injector import containers, providers

from core.services.brand_service import BrandService
from core.services.listing_service import ListingService
from core.services.vehicle_service import VehicleService
from infra.config import Settings
from infra.db.models.base import Base
from infra.db.repositories.listings import SqlAlchemyListingRepository
from infra.db.repositories.vehicles import SqlAlchemyVehicleRepository
from infra.db.service import DatabaseService
from infra.factory.clients.http import ClientType, HttpClientFactory
from infra.factory.logger import LoggerFactory
from infra.factory.providers.webdriver_cookie_provider import WebdriverCookieProvider
from infra.factory.webdriver import WebdriverFactory
from infra.io.file_service import LocalFileService
from infra.scraping.listing_scraper import ListingScraper
from infra.scraping.vehicle_scraper import VehicleScraper


def init_database(db_service):
    db_service.create_all_tables(Base)
    return db_service


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.from_pydantic(Settings())
    config.from_yaml(
        os.path.join(
            config.project_root.provided(), f"infra/configs/{config.environment.provided()}.yml"
        )
    )

    # database
    db_service = providers.Singleton(
        DatabaseService,
        connection_string=config.database.url.provided(),
        echo=config.database.echo.provided(),
    )
    init_db = providers.Resource(init_database, db_service=db_service)

    # repositories
    listing_repository = providers.Singleton(
        SqlAlchemyListingRepository,
        db_service=db_service,
    )
    vehicle_repository = providers.Singleton(
        SqlAlchemyVehicleRepository,
        db_service=db_service,
    )

    # factories
    logger_factory = providers.Singleton(
        LoggerFactory,
        log_level=config.logging.log_level.as_int(),
        format=config.logging.format.provided(),
    )
    webdriver_factory = providers.Singleton(
        WebdriverFactory,
        chrome_options=config.webdriver.chrome_options.provided(),
        use_stealth=config.webdriver.use_stealth.provided(),
        logger_factory=logger_factory,
        timeout_seconds=config.webdriver.timeout_seconds.provided(),
        chrome_binary_path=config.webdriver.chrome_binary_path.provided(),
        chromedriver_path=config.webdriver.chromedriver_path.provided(),
    )
    cookie_provider = providers.Singleton(
        WebdriverCookieProvider,
        webdriver_factory=webdriver_factory,
    )
    http_client_factory = providers.Singleton(
        HttpClientFactory,
        url=config.http.url.provided(),
        headers=config.http.headers.provided(),
        logger_factory=logger_factory,
        cookie_provider=cookie_provider,
        client_type=config.http.client_type.as_(lambda x: ClientType(x)),
    )

    # services
    file_service = providers.Selector(
        config.file_service.type,
        local=providers.Singleton(
            LocalFileService,
            basedir=config.project_root.provided(),
            logger_factory=logger_factory,
        ),
        # s3=providers.Singleton(
        #     S3FileService,
        #     logger_factory=logger_factory,
        # ),
    )
    brand_service = providers.Singleton(
        BrandService,
        file_service=file_service,
        brands_path=config.resources.brands.provided(),
    )
    listing_service = providers.Singleton(
        ListingService,
        repo=listing_repository,
    )
    vehicle_service = providers.Singleton(
        VehicleService,
        repo=vehicle_repository,
    )
    load_brands = providers.Resource(
        lambda service: service.read_brands(),
        service=brand_service,
    )

    # scrapers
    listing_scraper = providers.Singleton(
        ListingScraper,
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        min_req_delay=config.scrapers.listing_scraper.min_req_delay.provided(),
        max_req_delay=config.scrapers.listing_scraper.max_req_delay.provided(),
        timeout=config.scrapers.listing_scraper.timeout.provided(),
    )
    vehicle_scraper = providers.Singleton(
        VehicleScraper,
        logger_factory=logger_factory,
        http_client_factory=http_client_factory,
        min_req_delay=config.scrapers.vehicle_scraper.min_req_delay.provided(),
        max_req_delay=config.scrapers.vehicle_scraper.max_req_delay.provided(),
        timeout=config.scrapers.vehicle_scraper.timeout.provided(),
        reinit_session_every=config.scrapers.vehicle_scraper.reinit_session_every.provided(),
    )
