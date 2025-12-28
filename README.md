# CarScout Pipeline

Local web scraping pipeline for vehicle listings published on [olx.ba](https://olx.ba).

## Overview

CarScout Pipeline extracts, processes, and stores vehicle listing data through a two-stage scraping workflow:

1. **Listings Stage**: Scrapes listing metadata (title, price, URL) for each vehicle brand
2. **Vehicles Stage**: Extracts detailed vehicle specifications from individual listing pages

All scraping runs are tracked via `run_id` for data lineage, reproducibility, and batch processing.

---

## Architecture

- **Clean Architecture**: Clear separation of business logic (`core/`) from infrastructure (`infra/`)
- **Dependency Injection**: Container-based DI using `dependency-injector`
- **Repository Pattern**: Protocol-based repository interfaces with SQLAlchemy implementations
- **Workflow Orchestration**: Apache Airflow DAGs for scheduling, retries, and observability
- **Entity-First Design**: Domain entities modeled as dataclasses with business rules

---

## Tech Stack

- **Python 3.11+** with [uv](https://github.com/astral-sh/uv) for dependency management
- **Apache Airflow** for orchestration and execution
- **SQLAlchemy** for database access
- **Selenium** for JavaScript-heavy scraping
- **Docker & Docker Compose** for local orchestration (Airflow, database, browser tooling)

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- Docker (required for Airflow-based execution)

---

### Installation

1. **Clone the repository and install dependencies**
   ```bash
   git clone <repository-url>
   cd carscout_pipe
   uv sync
