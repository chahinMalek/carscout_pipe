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
- Configuration loaded from `infra/config/config.yml` with env var overrides (`REDIS_URL`, `CHROME_BINARY_PATH`, etc.)
- Factories use Singleton pattern (webdriver_factory, logger_factory, http_client_factory)
- Repositories/services auto-injected into Celery tasks via `@inject` + `Provide[Container.x]`
- Initialize container with `container.init_resources()` to create DB tables

### Data Flow Pattern
1. **Listings Pipeline**: Brand → ListingScraper → Listing entities → ListingRepository (stored with `run_id`)
2. **Vehicles Pipeline**: Query listings without vehicles by `run_id` → VehicleScraper → Vehicle entities → VehicleRepository
3. **Run ID Tracking**: Each Celery task ID becomes the `run_id` for batch tracking

### Entity-ORM Mapping
- Core entities (`Listing`, `Vehicle`) are dataclasses with business logic (e.g., `parsed_price()`, `from_dict()`)
- DB models (`ListingModel`, `VehicleModel`) in `infra/db/models/` are SQLAlchemy ORM classes
- Repositories handle conversion: `_convert_entity_to_orm()` / `_convert_orm_to_entity()`

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
```bash
# Via API
POST http://localhost:8000/api/v1/tasks/listings   # Scrape listings
POST http://localhost:8000/api/v1/tasks/vehicles   # Scrape vehicle details
POST http://localhost:8000/api/v1/tasks/pipeline   # Full pipeline (chained)

# Via CLI scripts
python scripts/process_listings.py
python scripts/process_vehicles.py
python scripts/run_pipeline.py
```

## Code Conventions

### Repository Pattern
- Core repos are Protocols with abstract methods (no implementation)
- Concrete implementations in `infra/db/repositories/` with `SqlAlchemy` prefix
- Always use context managers: `with self.db_service.create_session() as session:`
- Queries use SQLAlchemy 2.0 style: `select(Model).filter_by(...)` not legacy query API

### Scraper Pattern
- Inherit from `infra.scraping.base.Scraper`
- Implement `scraper_id` property and `run()` method as generator
- Use `logger_factory.create(self.scraper_id)` for scoped logging
- Respect rate limiting from config: `scrapers.listing_scraper.min_req_delay`

### Service Layer
- Services in `core/services/` are thin: validation + repository calls
- Static factory methods for entity creation (e.g., `ListingService.create_listing()`)
- No business logic in services—keep it in entities or utils

### Testing Conventions
- Use `pytest` with mocks for repository dependencies
- Mock repos with `Mock(spec=ListingRepository)` to enforce protocol
- Test structure: `tests/services/test_<service_name>.py` with nested test classes
- Fixtures for common setup (mock_repo, service instances)

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

## File References
- **Container wiring**: [infra/containers.py](infra/containers.py)
- **Task definitions**: [worker/tasks.py](worker/tasks.py)
- **API routes**: [app/api.py](app/api.py)
- **Repository protocols**: [core/repositories/](core/repositories/)
- **Config schema**: [infra/config/config.yml](infra/config/config.yml)
- **Test examples**: [tests/services/test_listing_service.py](tests/services/test_listing_service.py)

## Common Pitfalls
- Don't forget `container.init_resources()` before accessing DB repos
- Use `uv run` prefix for all Python commands to ensure correct virtualenv
- Celery tasks must be imported in `worker/tasks.py` to be discoverable
- Entity `__post_init__` strips whitespace—ensure this in new entities
- SQLAlchemy sessions must be closed (use context managers, not manual close)
