from datetime import UTC, datetime, timedelta

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

        fetched_run = repo.get(run.id)
        assert fetched_run.status == RunStatus.FAILED

    def test_update_fail(self, repo):
        run = Run(id="unknown", started_at=datetime.now(UTC))
        assert repo.get("unknown") is None
        with pytest.raises(ValueError):
            repo.update(run)

    def test_get_non_existent(self, repo):
        assert repo.get("non-existent") is None

    def test_search(self, repo):
        now = datetime.now(UTC)
        r1 = Run(id="run-001", started_at=now, status=RunStatus.SUCCESS)
        r2 = Run(id="run-002", started_at=now - timedelta(days=1), status=RunStatus.FAILED)
        r3 = Run(id="test-run-003", started_at=now - timedelta(days=2), status=RunStatus.SUCCESS)

        repo.add(r1)
        repo.add(r2)
        repo.add(r3)

        # search by status
        results, count = repo.search(status=RunStatus.SUCCESS.value)
        assert count == 2
        assert {r.id for r in results} == {"run-001", "test-run-003"}

        # search by id pattern
        results, count = repo.search(id_pattern="test")
        assert count == 1
        assert results[0].id == "test-run-003"

        # search with pagination
        results, count = repo.search(limit=1, offset=0)
        assert len(results) == 1
        assert count == 3

    def test_get_run_metrics(self, repo):
        now = datetime.now(UTC)
        # completed run with some metrics
        run = Run(
            id="run-metrics",
            started_at=now - timedelta(minutes=10),
            status=RunStatus.SUCCESS,
            completed_at=now,
            listings_scraped=100,
            vehicles_scraped=50,
            errors_count=2,
        )
        repo.add(run)

        # incomplete run (should be ignored by metrics)
        repo.add(Run(id="run-incomplete", started_at=now))

        metrics = repo.get_run_metrics()
        assert len(metrics) == 1
        m = metrics[0]
        assert m["id"] == "run-metrics"
        assert m["duration_seconds"] == 600.0
        assert m["listings"] == 100
        assert m["vehicles"] == 50
        assert m["errors"] == 2
