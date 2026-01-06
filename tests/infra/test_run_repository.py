from datetime import UTC, datetime

import pytest

from core.entities.run import Run, RunStatus
from infra.db.repositories.runs import SqlAlchemyRunRepository


@pytest.mark.integration
class TestSqlAlchemyRunRepository:
    @pytest.fixture
    def repo(self, in_memory_db):
        return SqlAlchemyRunRepository(in_memory_db)

    def test_add_run(self, repo):
        run = Run(id="test-run-1", started_at=datetime.now(UTC))
        saved_run = repo.add(run)

        assert saved_run.id == "test-run-1"
        assert saved_run.status == RunStatus.RUNNING
        assert repo.get("test-run-1").id == "test-run-1"

    def test_update_run(self, repo):
        run = Run(id="test-run-1", started_at=datetime.now(UTC))
        repo.add(run)

        run.fail("Something went wrong")
        updated_run = repo.update(run)

        assert updated_run.status == RunStatus.FAILED
        assert updated_run.last_error_message == "Something went wrong"
        assert updated_run.completed_at is not None

        fetched_run = repo.get("test-run-1")
        assert fetched_run.status == RunStatus.FAILED
