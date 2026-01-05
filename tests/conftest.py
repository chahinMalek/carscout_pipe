from unittest.mock import Mock

import pytest

from infra.db.models.base import Base
from infra.db.models.listing import ListingModel  # noqa
from infra.db.models.run import RunModel  # noqa
from infra.db.models.vehicle import VehicleModel  # noqa
from infra.db.service import DatabaseService
from infra.factory.logger import LoggerFactory


@pytest.fixture
def mock_logger_factory():
    factory = Mock(spec=LoggerFactory)
    factory.create.return_value = Mock()
    return factory


@pytest.fixture
def in_memory_db():
    db_service = DatabaseService("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(db_service.engine)
    yield db_service
    db_service.engine.dispose()
