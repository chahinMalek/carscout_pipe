# CarScout Pipeline

Local web scraping pipeline for vehicle listings published on [olx.ba](https://olx.ba).

## Overview

CarScout Pipeline extracts, processes, and stores vehicle listing data through a two-stage scraping workflow:

1. **Listings Stage**: Scrapes listing metadata (title, price, URL) for each vehicle brand
2. **Vehicles Stage**: Extracts detailed vehicle specifications from individual listing pages

All scraping runs are tracked via `run_id` for data lineage and batch processing.

## Architecture

- **Clean Architecture**: Separation of business logic (`core/`) from infrastructure (`infra/`)
- **Dependency Injection**: Container-based DI with `dependency-injector`
- **Repository Pattern**: Protocol-based interfaces with SQLAlchemy implementations
- **Task Queue**: Celery + Redis for distributed, asynchronous processing
- **Entity-First Design**: Domain models as dataclasses with business logic

## Tech Stack

- **Python 3.11+** with [uv](https://github.com/astral-sh/uv) for dependency management
- **FastAPI** for REST API
- **Celery** for background task processing
- **SQLAlchemy 2.0** for database operations
- **Selenium** for JavaScript-heavy scraping
- **Redis** as Celery message broker

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker (optional, for Redis and containerized deployment)

### Installation

1. **Clone and install dependencies**
   ```bash
   git clone <repository-url>
   cd carscout_pipe
   uv sync
   ```

2. **Configure environment** (optional - uses sensible defaults)

   Override via environment variables:
   ```bash
   export REDIS_URL="redis://localhost:6379/0"
   export CHROME_BINARY_PATH="/path/to/chrome"
   export CHROMEDRIVER_PATH="/path/to/chromedriver"
   ```

3. **Start Redis**
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

### Running the Pipeline

**Option 1: Via API** (recommended)

```bash
# Terminal 1: Start API server
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Celery worker
celery -A worker.main worker --loglevel=info

# Terminal 3: Trigger pipeline
curl -X POST http://localhost:8000/api/v1/tasks/pipeline
```

**Option 2: Docker Compose** (production)

```bash
docker-compose up
# API available at http://localhost:8000
```

## API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tasks/listings` | Scrape all brands (parallel tasks) |
| `POST` | `/api/v1/tasks/listings/{brand_slug}` | Scrape single brand |
| `POST` | `/api/v1/tasks/vehicles` | Scrape vehicle details for latest run |
| `POST` | `/api/v1/tasks/pipeline` | Full pipeline (listings → vehicles) |
| `GET` | `/api/v1/tasks/{task_id}` | Check task status |
| `GET` | `/health` | Health check |

**Example:**
```bash
# Start full pipeline
curl -X POST http://localhost:8000/api/v1/tasks/pipeline

# Check task status
curl http://localhost:8000/api/v1/tasks/{task_id}
```

## Task Management

Monitor and manage Celery tasks:

```bash
# List active tasks
celery -A worker.main inspect active

# List registered tasks
celery -A worker.main inspect registered

# Purge task queue
celery -A worker.main purge

# Real-time task events
celery -A worker.main events
```

## Project Structure

```
carscout_pipe/
├── core/               # Business logic (domain-driven)
│   ├── entities/       # Domain models (dataclasses)
│   ├── repositories/   # Repository protocols (interfaces)
│   ├── services/       # Business services
│   └── utils/          # Domain utilities
├── infra/              # Infrastructure implementations
│   ├── db/             # SQLAlchemy models & repositories
│   ├── scraping/       # Web scraper implementations
│   ├── factory/        # Factory patterns (logger, webdriver, etc.)
│   └── containers.py   # Dependency injection container
├── app/                # Application entry points
│   └── api.py          # FastAPI routes
├── worker/             # Celery task definitions
├── tests/              # Test suite (unit + integration)
└── resources/seeds/    # Seed data (brands CSV)
```

## Configuration

Configuration is managed via [`infra/config/config.yml`](infra/config/config.yml) with environment variable overrides:

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `CHROME_BINARY_PATH` | Chrome binary path | Auto-detected |
| `CHROMEDRIVER_PATH` | ChromeDriver path | Auto-detected |

Key config sections:
- **scrapers**: Rate limiting (`min_req_delay`, `max_req_delay`)
- **webdriver**: Chrome options (headless, stealth mode)
- **resources.brands**: CSV seed file path (`brands_tiny.csv` for dev)

## Development

### Local Debugging (3-Terminal Setup)

**Terminal 1** - Redis:
```bash
docker run -p 6379:6379 redis:alpine
```

**Terminal 2** - FastAPI (hot reload):
```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3** - Celery worker (verbose logs):
```bash
celery -A worker.main worker --loglevel=debug
```

### Testing

```bash
uv run pytest                    # Run all tests
uv run pytest tests/services/    # Unit tests only
uv run pytest -m integration     # Integration tests only
uv run pytest -k test_name       # Specific test
```

### Code Quality

```bash
uv run ruff check .              # Lint code
uv run ruff check --fix .        # Auto-fix issues
uv run ruff format .             # Format code
```

### Managing Dependencies

```bash
uv add package-name              # Add runtime dependency
uv add --dev package-name        # Add dev dependency
uv sync --upgrade                # Update all dependencies
```

## Troubleshooting

**Issue: Celery tasks not discovered**
- Ensure tasks are imported in [`worker/tasks.py`](worker/tasks.py)
- Verify container wiring: `container.wire(packages=["worker"])`

**Issue: Database not initialized**
- Call `container.init_resources()` before accessing repositories
- Check DB file exists: `data/carscout_*.db`

**Issue: ChromeDriver errors**
- Set `CHROME_BINARY_PATH` and `CHROMEDRIVER_PATH` environment variables
- Ensure ChromeDriver version matches installed Chrome version

**Issue: Redis connection refused**
- Verify Redis is running: `docker ps` or `redis-cli ping`
- Check `REDIS_URL` environment variable

## Contributing

1. Follow Clean Architecture principles (keep `core/` free of infrastructure imports)
2. Use Protocol interfaces for all repository definitions
3. Write tests for new features (see [`tests/`](tests/) for examples)
4. Run linting before committing: `uv run ruff check --fix .`
5. Update tests when changing repository or entity interfaces

## License

TBA
