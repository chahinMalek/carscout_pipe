# carscout_pipe

Car listing scraping and processing pipeline built with modern Python best practices.

## Features

- **Modern Python Setup**: Using `uv` for fast, reliable dependency management
- **Dependency Injection**: Clean architecture with dependency-injector
- **Web Scraping**: Scrapy and Selenium for comprehensive data extraction
- **Task Queue**: Celery with Redis for distributed task processing
- **Database**: SQLAlchemy for relational data storage
- **Data Processing**: Pandas for efficient data manipulation

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd carscout_pipe
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Configure environment** (if needed)
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   # Using uv (recommended)
   uv run carscout

   # Or activate environment first
   source .venv/bin/activate
   carscout
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t carscout-pipe .
   ```

2. **Run the container**
   ```bash
   docker run -it --rm \
     --env-file .env \
     carscout-pipe
   ```

3. **Using Docker Compose** (recommended for production)
   ```yaml
   # docker-compose.yml example
   services:
     app:
       build: .
       env_file: .env
       depends_on:
         - redis

     redis:
       image: redis:7-alpine
   ```

## Project Structure

```
carscout_pipe/
├── app/              # Application entry points
├── core/             # Business logic and domain entities
│   ├── entities/     # Domain models
│   ├── repositories/ # Repository interfaces
│   ├── services/     # Business services
│   └── utils/        # Core utilities
├── infra/            # Infrastructure layer
│   ├── db/           # Database implementations
│   ├── factory/      # Factory patterns
│   ├── scraping/     # Web scraping implementations
│   └── utils/        # Infrastructure utilities
├── scripts/          # Standalone scripts
├── tasks/            # Celery tasks
├── tests/            # Test suite
└── data/             # Data files and seeds
```

## Development

## Local debugging

Run Locally for Better Debugging (Recommended)
**Terminal 1** - Start Redis:

```
docker run -p 6379:6379 redis:alpine
```

**Terminal 2** - Start FastAPI with debugger support:

```
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3** - Start Celery worker with detailed logs:

```
celery -A worker.main worker --loglevel=debug
```

### Running Tests
```bash
uv run pytest
```

### Code Linting and Formatting
```bash
uv run ruff check .           # Check code quality
uv run ruff check --fix .     # Auto-fix issues
uv run ruff format .          # Format code
```

### Adding Dependencies
```bash
uv add package-name           # Add runtime dependency
uv add --dev package-name     # Add dev dependency
uv sync --upgrade             # Update all dependencies
```

## License

TBA
