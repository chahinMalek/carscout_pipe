# CarScout Pipeline

Local web scraping pipeline for vehicle listings published on [olx.ba](https://olx.ba).

## Overview

CarScout Pipeline extracts, processes, and stores vehicle listing data through a two-stage scraping workflow:

1. **Listings Stage**: Scrapes listing metadata (title, price, URL) for each vehicle brand
2. **Vehicles Stage**: Extracts detailed vehicle specifications from individual listing pages

All scraping runs are tracked via `run_id` for data lineage, reproducibility, and batch processing. The pipeline includes built-in metadata tracking for monitoring progress, error rates, and success metrics.

---

## Architecture

- **Clean Architecture**: Clear separation of business logic (`core/`) from infrastructure (`infra/`)
- **Dependency Injection**: Container-based DI using `dependency-injector`
- **Repository Pattern**: Protocol-based repository interfaces with SQLAlchemy implementations
- **Workflow Orchestration**: Apache Airflow DAGs for scheduling, retries, and observability
- **Entity-First Design**: Domain entities modeled as dataclasses with business rules
- **Resilient Scraping**:
  - Selenium with stealth mode for JavaScript-heavy listing pages
  - Resilient HTTP clients with session management and retries for API endpoints
  - Configurable delays and timeouts to respect rate limits

---

## Tech Stack

- **Python 3.11+** with [uv](https://github.com/astral-sh/uv) for dependency management
- **Apache Airflow** for orchestration and execution
- **SQLAlchemy** for database access
- **Selenium** (Listings) & **Requests/HTTPX** (Vehicle Data)
- **Docker & Docker Compose** for local orchestration (Airflow, database, browser tooling)
- **SQLite** for zero-setup local storage

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Docker (required for Airflow-based execution)

### Installation

1. **Clone the repository and install dependencies**
   ```bash
   git clone <repository-url>
   cd carscout_pipe
   uv sync
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (default local settings usually work out of the box)
   ```

3. **Start Airflow**
   ```bash
   docker-compose up -d
   ```

4. **Access Airflow UI**
   - Open `http://localhost:8080`
   - Login with `admin` / `admin`
   - Enable and trigger the `carscout_pipeline` DAG

---

## Roadmap

### Improvements
- **Architecture**: Upgrade to SQLAlchemy 2.0+ & add Alembic migrations
- **Observability**: Improve error handling and observability in DAG
- **CI/CD**: GitHub Actions CI workflow
- **Quality**: Add badges (tests, coverage, code quality) & architecture diagram

### Planned Features
- **Interface**: Simple CLI entrypoint & Streamlit dashboard
- **Proxies**: Integrating proxy providers (opt-in via configs)
  - Adapters for ZenRows, ScrapingBee, and custom lists
  - Health checks and automatic fallback capabilities
- **Data**: Add data export capabilities (CSV, JSON, Parquet)

### Potential Features
- **Modernization**: Migration to Playwright for faster scraping
- **Storage**: DuckDB alternative for analytical queries
