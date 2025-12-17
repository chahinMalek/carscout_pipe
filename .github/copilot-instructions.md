# CarScout Pipeline - AI Agent Instructions

## Project Overview
Web scraping pipeline for vehicle listings from olx.ba. Built with Clean Architecture (core/infra separation), dependency injection, Celery task queue, and FastAPI.

## Architecture & Design Patterns

### Clean Architecture Layers
- **core/**: Business logic with Protocol-based repository interfaces. Domain entities are dataclasses, services are thin wrappers around repositories.
- **infra/**: Implementation details (DB, scraping, factories). Implements core protocols with concrete adapters (e.g., `SqlAlchemyListingRepository` implements `ListingRepository` protocol).
- **app/**: Entry points (FastAPI API, CLI via `carscout` command).
- **worker/**: Celery tasks that wire the container and orchestrate scraping workflows.

### Dependency Injection (dependency-injector)
All dependencies wired through `infra/containers.py`:

#### Container Structure
- **Configuration**: `config` provider loads from YAML + env var overrides
- **Database**: `db_service` (Singleton), `init_db` (Resource - creates tables)
- **Repositories**: `listing_repository`, `vehicle_repository` (Singleton)
- **Factories**: `logger_factory`, `webdriver_factory`, `http_client_factory` (Singleton)
- **Services**: `listing_service`, `vehicle_service`, `brand_service`, `file_service` (Singleton)
- **Scrapers**: `listing_scraper`, `vehicle_scraper` (Singleton)
- **Resources**: `load_brands` (Resource - loads CSV on init)

#### Configuration Overrides (Environment Variables)
```python
# In containers.py - priority: ENV VAR > config.yml
config.redis.url.from_env("REDIS_URL", config.redis.url())
config.webdriver.chrome_binary_path.from_env("CHROME_BINARY_PATH", ...)
config.webdriver.chromedriver_path.from_env("CHROMEDRIVER_PATH", ...)
```

#### Accessing Config in Application Code
```python
# From container
container.config.redis.url()           # Get redis URL
container.config.scrapers.listing_scraper.min_req_delay()  # Get nested config
```

#### Task Injection Pattern
```python
@celery_app.task(bind=True)  # bind=True gives access to self.request.id
@inject
def process_listings_for_brand(
    self,
    brand_slug: str,
    listing_scraper: ListingScraper = Provide[Container.listing_scraper],
    listing_service: ListingService = Provide[Container.listing_service],
):
    run_id = str(self.request.id).strip()  # Task ID becomes run_id
    # ... task logic
```

#### Initialization Sequence
```python
# In worker/main.py or app/api.py
container = Container()
container.init_resources()  # Creates DB tables, loads brands CSV
container.wire(packages=["worker"])  # Wire for Celery tasks
```

### Data Flow Pattern
1. **Listings Pipeline**: Brand → ListingScraper → Listing entities → ListingRepository (stored with `run_id`)
2. **Vehicles Pipeline**: Query listings without vehicles by `run_id` → VehicleScraper → Vehicle entities → VehicleRepository
3. **Run ID Tracking**: Each Celery task ID becomes the `run_id` for batch tracking

### Entity-ORM Mapping
- Core entities (`Listing`, `Vehicle`) are dataclasses with business logic (e.g., `parsed_price()`, `from_dict()`)
- DB models (`ListingModel`, `VehicleModel`) in `infra/db/models/` are SQLAlchemy ORM classes
- Repositories handle conversion: `_convert_entity_to_orm()` / `_convert_orm_to_entity()`

#### Entity Pattern (Core Domain Objects)
```python
from dataclasses import dataclass, fields
from datetime import datetime

@dataclass
class Listing:
    id: str
    url: str
    title: str
    price: str
    visited_at: datetime | None = None
    run_id: str | None = None

    def __post_init__(self):
        """Auto-cleanup: strip whitespace from string fields."""
        self.id = self.id.strip()
        self.title = self.title.strip()
        self.url = self.url.strip()
        self.price = self.price.strip()
        if self.run_id:
            self.run_id = self.run_id.strip()
        if isinstance(self.visited_at, str):
            self.visited_at = datetime.fromisoformat(self.visited_at)

    @classmethod
    def from_dict(cls, data: dict) -> 'Listing':
        """Factory method for safe instantiation from dicts."""
        field_names = {f.name for f in fields(cls)}
        _d = {k: v for k, v in data.items() if k in field_names}
        return cls(**_d)

    def parsed_price(self) -> tuple[float, str] | None:
        """Business logic: parse price string to (amount, currency)."""
        return parse_price_str(self.price)
```

#### Key Entity Conventions
- **Dataclasses**: All entities are `@dataclass` (not Pydantic, not plain classes)
- **`__post_init__`**: Use for data normalization (strip whitespace, type conversions)
- **`from_dict` classmethod**: Safe construction from external data (filters unknown fields)
- **Business methods**: Keep domain logic in entities (e.g., `parsed_price()`, `timedelta_since_visit()`)
- **Immutability**: Prefer immutable entities where possible (use `frozen=True` if appropriate)

## Development Workflows

### Local Setup (uv package manager)
```bash
uv sync                    # Install dependencies
uv run carscout            # Run CLI (entry point in pyproject.toml)
uv run pytest              # Run tests
uv run ruff check --fix .  # Auto-fix linting
uv run ruff format .       # Format code
```

### Local Debugging (3-terminal setup)
```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:alpine

# Terminal 2: FastAPI (with reload for debugging)
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Celery worker (verbose logging)
celery -A worker.main worker --loglevel=debug
```

### Docker Deployment
```bash
docker-compose up          # Runs redis, celery-worker, api services
```
Volumes mounted for hot-reload: app/, core/, infra/, worker/, resources/, data/

### Running Tasks

#### Via API Endpoints
```bash
# Scrape listings for all brands (spawns parallel tasks)
POST http://localhost:8000/api/v1/tasks/listings

# Scrape listings for single brand
POST http://localhost:8000/api/v1/tasks/listings/{brand_slug}

# Scrape vehicle details for a run
POST http://localhost:8000/api/v1/tasks/vehicles

# Full pipeline (listings → vehicles, chained)
POST http://localhost:8000/api/v1/tasks/pipeline

# Check task status
GET http://localhost:8000/api/v1/tasks/{task_id}

# Health check
GET http://localhost:8000/health
```

#### Via CLI Scripts
```bash
uv run python scripts/process_listings.py    # Process all brands
uv run python scripts/process_vehicles.py    # Process vehicle details
uv run python scripts/run_pipeline.py        # Full pipeline
```

#### Task Monitoring (Celery)
```bash
# List active tasks
celery -A worker.main inspect active

# List registered tasks
celery -A worker.main inspect registered

# Purge all tasks from queue
celery -A worker.main purge

# Monitor task events in real-time
celery -A worker.main events
```

## Code Conventions

### Repository Pattern
- **Core repos are Protocols** with abstract methods (no implementation) in `core/repositories/`
- **Concrete implementations** in `infra/db/repositories/` with `SqlAlchemy` prefix
- Always use context managers: `with self.db_service.create_session() as session:`
- Queries use SQLAlchemy 2.0 style: `select(Model).filter_by(...)` not legacy query API

#### Repository Implementation Template
```python
from core.repositories.listing_repository import ListingRepository
from core.entities.listing import Listing
from infra.db.models.listing import ListingModel
from infra.db.service import DatabaseService
from sqlalchemy import select

class SqlAlchemyListingRepository(ListingRepository):
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def _convert_orm_to_entity(self, orm: ListingModel) -> Listing:
        return Listing(
            id=orm.listing_id,
            url=orm.url,
            title=orm.title,
            price=orm.price,
            visited_at=orm.visited_at,
            run_id=orm.run_id,
        )

    def _convert_entity_to_orm(self, entity: Listing) -> ListingModel:
        return ListingModel(
            listing_id=entity.id,
            url=entity.url,
            title=entity.title,
            price=entity.price,
            visited_at=entity.visited_at,
            run_id=entity.run_id,
        )

    def add(self, listing: Listing) -> Listing:
        with self.db_service.create_session() as session:
            record = self._convert_entity_to_orm(listing)
            session.add(record)
            session.commit()
            session.refresh(record)  # Get auto-generated fields
            return self._convert_orm_to_entity(record)
```

#### Common Query Patterns
```python
# Simple filter
query = select(Model).filter_by(id=value)
result = session.scalars(query).first()

# Order by + limit
query = select(Model).order_by(Model.created_at.desc()).limit(10)
results = session.scalars(query).all()

# Left join (e.g., listings without vehicles)
query = (
    select(ListingModel)
    .outerjoin(ListingModel.vehicle)
    .filter(VehicleModel.listing_id.is_(None))
)
results = session.execute(query).scalars().all()
```

### Scraper Pattern
- Inherit from `infra.scraping.base.Scraper`
- Implement `scraper_id` property and `run()` method as generator
- Logger auto-created in base class: `self._logger`
- Respect rate limiting from config: `scrapers.listing_scraper.min_req_delay`

#### Scraper Implementation Template
```python
from infra.scraping.base import Scraper
from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory

class ListingScraper(Scraper):
    def __init__(
        self,
        logger_factory: LoggerFactory,
        webdriver_factory: WebdriverFactory,
        min_req_delay: float,
        max_req_delay: float,
        timeout: int,
    ):
        super().__init__(logger_factory)  # Creates self._logger
        self.webdriver_factory = webdriver_factory
        self.min_req_delay = min_req_delay
        self.max_req_delay = max_req_delay
        self.timeout = timeout

    @property
    def scraper_id(self) -> str:
        return "listing_scraper"

    def run(self, brand: Brand):
        """Generator that yields Listing entities."""
        self._logger.info(f"Starting scrape for {brand.name}")

        # Rate limiting
        time.sleep(random.uniform(self.min_req_delay, self.max_req_delay))

        # Scraping logic
        for item in self._scrape_page(brand.url):
            yield Listing(
                id=item["id"],
                url=item["url"],
                title=item["title"],
                price=item["price"],
                visited_at=datetime.now(UTC),
            )
```

#### Error Handling in Scrapers
```python
from core.exceptions import PageNotFoundError

try:
    # scraping logic
    pass
except PageNotFoundError as e:
    self._logger.error(f"Page not found: {e.message}")
    raise
except Exception as e:
    self._logger.exception(f"Unexpected error: {e}")
    raise
```

### Service Layer
- Services in `core/services/` are thin: validation + repository calls
- Static factory methods for entity creation (e.g., `ListingService.create_listing()`)
- No business logic in services—keep it in entities or utils

#### Service Implementation Pattern
```python
from core.repositories.listing_repository import ListingRepository
from core.entities.listing import Listing

class ListingService:
    def __init__(self, repo: ListingRepository):
        self.repo = repo

    @staticmethod
    def create_listing(data: dict) -> Listing:
        """Factory method for creating entities from dicts."""
        return Listing.from_dict(data)

    def insert_listing(self, listing: Listing) -> Listing:
        """Business validation + delegation to repo."""
        return self.repo.add(listing)

    def find_latest(self, listing_id: str) -> Listing | None:
        """Simple delegation to repository."""
        return self.repo.find_latest(listing_id)
```

### Testing Conventions

### Test Organization
- **Unit tests**: `tests/services/` - Test business logic with mocked dependencies
- **Integration tests**: `tests/infra/` - Test infrastructure with real DB (in-memory SQLite)
- Test files named `test_<module_name>.py` matching the module they test
- Group related tests in nested classes: `class TestCreateListing:`, `class TestInsertListing:`

### Test Markers (pytest.ini)
```python
@pytest.mark.unit          # Fast tests, no external dependencies
@pytest.mark.integration   # Real DB/file system interactions
@pytest.mark.slow          # Long-running tests (scrapers, etc.)
```

### Fixtures (tests/conftest.py)
- `mock_logger_factory`: Mock logger for unit tests
- `in_memory_db`: SQLite in-memory DB with tables created, disposed after test
- Use `@pytest.fixture` for reusable test setup (repos, services, sample data)

### Unit Test Pattern (Service Layer)
```python
from unittest.mock import Mock
import pytest

@pytest.fixture
def mock_repo():
    return Mock(spec=ListingRepository)  # Enforce protocol

@pytest.fixture
def service(mock_repo):
    return ListingService(repo=mock_repo)

class TestInsertListing:
    def test_insert_listing_success(self, service, mock_repo):
        listing = Listing(id="test", url="...", title="...", price="...")
        mock_repo.add.return_value = listing

        result = service.insert_listing(listing)

        mock_repo.add.assert_called_once_with(listing)
        assert result == listing
```

### Integration Test Pattern (Repository Layer)
```python
@pytest.mark.integration
class TestSqlAlchemyListingRepository:
    @pytest.fixture
    def repo(self, in_memory_db):
        return SqlAlchemyListingRepository(in_memory_db)

    @pytest.fixture
    def sample_listing(self):
        return Listing(id="listing-001", url="...", ...)

    def test_add_listing(self, repo, sample_listing, in_memory_db):
        result = repo.add(sample_listing)

        # Verify entity returned correctly
        assert result.id == sample_listing.id

        # Verify persisted to DB
        with in_memory_db.create_session() as session:
            orm_result = session.query(ListingModel).filter_by(
                listing_id=sample_listing.id
            ).first()
            assert orm_result is not None
```

### Best Practices
- **Isolation**: Each test should be independent (no shared state between tests)
- **AAA Pattern**: Arrange (setup), Act (execute), Assert (verify)
- **Descriptive Names**: `test_method_name_scenario_expected_behavior`
- **Mock Protocols**: Always use `Mock(spec=ProtocolClass)` to catch interface violations
- **Session Management**: Always use context managers for DB sessions in integration tests
- **Fixture Scope**: Default scope is function-level (runs before each test)

## Configuration Management

### YAML Config (`infra/config/config.yml`)
- Hierarchical config: db, redis, webdriver, http, scrapers, logging
- Environment variable overrides defined in `containers.py`:
  - `REDIS_URL`, `CHROME_BINARY_PATH`, `CHROMEDRIVER_PATH`
- Access via container: `container.config.redis.url()`

### Important Config Sections
- **webdriver.chrome_options**: Headless scraping with stealth mode
- **http.client_type**: "requests" or "httpx" (factory pattern)
- **resources.brands**: CSV seed file path (brands_tiny.csv for dev)
- **db.url**: SQLite by default (sqlite:///data/carscout_*.db)

## Key Integration Points

### Celery + Dependency Injection
- Tasks decorated with `@celery_app.task(bind=True)` and `@inject`
- Container wired in `worker/main.py`: `container.wire(packages=["worker"])`
- Task `self.request.id` becomes the `run_id` for data lineage

### Database Models & Relationships
- `ListingModel.listing_id` is ForeignKey to `VehicleModel.listing_id`
- One-to-many: Vehicle has many Listings (via `vehicle.listings` relationship)
- Always query by `run_id` to process batches atomically

### HTTP Client Factory
- Abstraction over requests/httpx via `ClientType` enum
- Cookie provider injects Selenium-obtained cookies for authenticated scraping
- Headers configured globally in config.yml

## Project Structure & File Organization

### Core Layer (Domain Logic)
- **entities/**: Domain models as dataclasses (`listing.py`, `vehicle.py`, `brand.py`)
- **repositories/**: Protocol interfaces (abstract methods only, no implementation)
- **services/**: Thin service layer (validation + delegation to repositories)
- **utils/**: Pure business logic utilities (`prices.py` - price parsing)
- **exceptions.py**: Custom exception classes (`PageNotFoundError`)

### Infrastructure Layer (Implementation Details)
- **db/models/**: SQLAlchemy ORM models (`listing.py`, `vehicle.py`)
- **db/repositories/**: Concrete repository implementations (`SqlAlchemy*` classes)
- **db/service.py**: Database connection management with session factory
- **scraping/**: Web scraper implementations (`listing_scraper.py`, `vehicle_scraper.py`)
- **scraping/base.py**: Base scraper class with logger injection
- **factory/**: Factory classes for creating instances (logger, webdriver, http client)
- **interfaces/**: Protocol definitions for infrastructure (`cookie_provider.py`, `http.py`)
- **io/**: File system operations (`file_service.py`)
- **utils/**: Infrastructure utilities (`parsing.py`, `timeout.py`)
- **containers.py**: Dependency injection container configuration
- **config/config.yml**: Application configuration (DB, Redis, scrapers, etc.)

### Application Layer (Entry Points)
- **app/api.py**: FastAPI REST API endpoints
- **app/cli.py**: Command-line interface (unused currently)

### Worker Layer (Background Tasks)
- **worker/main.py**: Celery app initialization + container wiring
- **worker/tasks.py**: Celery task definitions (must import all tasks here for discovery)

### Test Organization
- **tests/conftest.py**: Shared fixtures (`in_memory_db`, `mock_logger_factory`)
- **tests/services/**: Unit tests for service layer (mocked dependencies)
- **tests/infra/**: Integration tests for infrastructure (real DB, files)
- Test file naming: `test_<module_name>.py` mirrors the structure of the code

### Configuration & Data
- **resources/seeds/**: CSV files for seeding data (`brands.csv`, `brands_tiny.csv`)
- **data/**: SQLite database files (gitignored, created at runtime)
- **scripts/**: One-off utility scripts for running pipelines

## File References
- **Container wiring**: [infra/containers.py](infra/containers.py)
- **Task definitions**: [worker/tasks.py](worker/tasks.py)
- **API routes**: [app/api.py](app/api.py)
- **Repository protocols**: [core/repositories/](core/repositories/)
- **Config schema**: [infra/config/config.yml](infra/config/config.yml)
- **Test examples**: [tests/services/test_listing_service.py](tests/services/test_listing_service.py)

## Common Pitfalls & Best Practices

### Container & Dependency Injection
- ❌ Don't forget `container.init_resources()` before accessing DB repos
- ❌ Don't manually instantiate dependencies—use container injection
- ✅ Always use `@inject` decorator with `Provide[Container.x]` in tasks
- ✅ Wire container only once in entry points (worker/main.py, app/api.py)

### Database Operations
- ❌ Never manually close sessions—always use `with self.db_service.create_session() as session:`
- ❌ Don't use legacy SQLAlchemy query API (`.query(Model)`)—use `select(Model)`
- ✅ Always refresh ORM objects after insert: `session.refresh(record)`
- ✅ Use `session.scalars(query).first()` for single results, `.all()` for lists

### Celery Tasks
- ❌ Celery tasks must be imported in `worker/tasks.py` to be discoverable
- ❌ Don't forget `bind=True` in task decorator if you need task ID
- ✅ Always strip task IDs: `run_id = str(self.request.id).strip()`
- ✅ Use `@inject` decorator for dependency injection in tasks

### Entity Conventions
- ❌ Entity `__post_init__` strips whitespace—ensure this in new entities
- ❌ Don't bypass `from_dict()` when creating entities from external data
- ✅ Always validate required fields before entity creation
- ✅ Put business logic in entity methods, not in services

### Development Environment
- ❌ Use `uv run` prefix for all Python commands to ensure correct virtualenv
- ❌ Don't commit `data/*.db` files—they're gitignored
- ✅ Use `brands_tiny.csv` for fast local development
- ✅ Run linting before committing: `uv run ruff check --fix .`

### Testing
- ❌ Don't mock concrete implementations—mock Protocol interfaces
- ❌ Don't share state between tests (use fixtures with function scope)
- ✅ Use `@pytest.mark.integration` for tests that touch DB/filesystem
- ✅ Always test ORM-to-entity conversion in integration tests
