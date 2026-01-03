from datetime import datetime

import pytest

from core.entities.run import Run
from infra.db.models.run import RunModel
from infra.db.repositories.runs import SqlAlchemyRunRepository
from infra.db.service import DatabaseService


class TestSqlAlchemyRunRepository:
    @pytest.fixture(scope="function")
    def db_service(self):
        db_service = DatabaseService("sqlite:///:memory:")
        db_service.Base = RunModel
        db_service.create_all_tables(RunModel)
        return db_service

    @pytest.fixture(scope="function")
    def repo(self, db_service):
        return SqlAlchemyRunRepository(db_service)

    def test_add_run(self, repo):
        run = Run(id="test-run-1", started_at=datetime.utcnow())
        saved_run = repo.add(run)

        assert saved_run.id == "test-run-1"
        assert saved_run.status == "running"
        assert repo.get("test-run-1").id == "test-run-1"

    def test_update_run(self, repo):
        run = Run(id="test-run-1", started_at=datetime.utcnow())
        repo.add(run)

        run.fail("Something went wrong")
        updated_run = repo.update(run)

        assert updated_run.status == "failed"
        assert updated_run.last_error_message == "Something went wrong"
        assert updated_run.completed_at is not None

        fetched_run = repo.get("test-run-1")
        assert fetched_run.status == "failed"
