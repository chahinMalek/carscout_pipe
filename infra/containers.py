import os
from pathlib import Path

from dependency_injector import containers, providers

from core.services.brand_service import BrandService
from core.services.listing_service import ListingService
from core.services.vehicle_service import VehicleService
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


class Container(containers.DeclarativeContainer):
    environment = os.environ.get("ENVIRONMENT") or "development"
    project_root = str(Path(__file__).parent.parent.absolute())

    config = providers.Configuration()
    config.environment.from_value(environment)
    config.from_yaml(os.path.join(project_root, "infra/config/config.yml"))

    # Override config from environment variables if present
    config.redis.url.from_env("REDIS_URL", config.redis.url())
    config.webdriver.chrome_binary_path.from_env(
        "CHROME_BINARY_PATH", config.webdriver.chrome_binary_path()
    )
    config.webdriver.chromedriver_path.from_env(
        "CHROMEDRIVER_PATH", config.webdriver.chromedriver_path()
    )

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
        format=config.logging.format,
    )
    webdriver_factory = providers.Singleton(
        WebdriverFactory,
        chrome_options=config.webdriver.chrome_options,
        use_stealth=config.webdriver.use_stealth,
        logger_factory=logger_factory,
        timeout_seconds=config.webdriver.timeout_seconds,
        chrome_binary_path=config.webdriver.chrome_binary_path,
        chromedriver_path=config.webdriver.chromedriver_path,
    )
    cookie_provider = providers.Singleton(
        WebdriverCookieProvider,
        webdriver_factory=webdriver_factory,
    )
    http_client_factory = providers.Singleton(
        HttpClientFactory,
        url=config.http.url,
        headers=config.http.headers,
        logger_factory=logger_factory,
        cookie_provider=cookie_provider,
        client_type=config.http.client_type.as_(lambda x: ClientType(x)),
    )

    # services
    file_service = providers.Selector(
        config.file_service.type,
        local=providers.Singleton(
            LocalFileService,
            basedir=project_root,
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
        brands_path=config.resources.brands,
    )
    listing_service = providers.Singleton(
        ListingService,
        repo=listing_repository,
    )
    vehicle_service = providers.Singleton(
        VehicleService,
        repo=vehicle_repository,
    )

    # scrapers
    listing_scraper = providers.Singleton(
        ListingScraper,
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        min_req_delay=config.scrapers.listing_scraper.min_req_delay,
        max_req_delay=config.scrapers.listing_scraper.max_req_delay,
        timeout=config.scrapers.listing_scraper.timeout,
    )
    vehicle_scraper = providers.Singleton(
        VehicleScraper,
        logger_factory=logger_factory,
        http_client_factory=http_client_factory,
        min_req_delay=config.scrapers.vehicle_scraper.min_req_delay,
        max_req_delay=config.scrapers.vehicle_scraper.max_req_delay,
        timeout=config.scrapers.vehicle_scraper.timeout,
        reinit_session_every=config.scrapers.vehicle_scraper.reinit_session_every,
    )
