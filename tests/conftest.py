from datetime import UTC, datetime

import pytest

from infra.db.models.base import Base
from infra.db.service import DatabaseService


@pytest.fixture
def in_memory_db():
    db_service = DatabaseService("sqlite:///:memory:", echo=False)
    db_service.create_all_tables(Base)
    yield db_service
    db_service.engine.dispose()


@pytest.fixture
def sample_listing_data():
    return {
        "id": "test-listing-123",
        "url": "https://olx.ba/test-listing-123",
        "title": "Test Vehicle 2020",
        "price": "25000 KM",
        "visited_at": datetime.now(UTC),
        "run_id": "test-run-001",
    }


@pytest.fixture
def sample_vehicle_data():
    return {
        "id": "test-vehicle-456",
        "brand": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "mileage": 50000,
        "fuel_type": "Benzin",
        "transmission": "Automatik",
        "body_type": "Limuzina",
        "engine_size": 1800,
        "power": 140,
        "registration_until": datetime(2025, 12, 31),
        "visited_at": datetime.now(UTC),
        "run_id": "test-run-001",
    }
