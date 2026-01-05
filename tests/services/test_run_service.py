import datetime
from unittest.mock import MagicMock

import pytest

from core.entities.run import Run
from core.services.run_service import RunService


class TestRunService:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()

    @pytest.fixture
    def run_service(self, mock_repo):
        return RunService(mock_repo)

    def test_start_run_new(self, run_service, mock_repo):
        mock_repo.get.return_value = None
        mock_repo.add.side_effect = lambda x: x

        run = run_service.start_run("run-123")

        assert run.id == "run-123"
        assert run.started_at is not None
        mock_repo.add.assert_called_once()

    def test_start_run_existing(self, run_service, mock_repo):
        existing_run = Run(id="run-123", started_at=datetime.datetime.now())
        mock_repo.get.return_value = existing_run

        run = run_service.start_run("run-123")

        assert run == existing_run
        mock_repo.add.assert_not_called()

    def test_update_metrics(self, run_service, mock_repo):
        run = Run(id="run-123", started_at=datetime.datetime.now())
        mock_repo.get.return_value = run
        mock_repo.update.side_effect = lambda x: x

        run_service.update_metrics("run-123", num_listings=10, num_vehicles=5, num_errors=1)

        assert run.listings_scraped == 10
        assert run.vehicles_scraped == 5
        assert run.errors_count == 1
        mock_repo.update.assert_called_once_with(run)

    def test_update_metrics_not_found(self, run_service, mock_repo):
        mock_repo.get.return_value = None

        with pytest.raises(ValueError, match="Run run-123 not found"):
            run_service.update_metrics("run-123", num_listings=10)

    def test_get_run(self, run_service, mock_repo):
        run = Run(id="run-123", started_at=datetime.datetime.now())
        mock_repo.get.return_value = run

        result = run_service.get_run("run-123")
        assert result == run
        mock_repo.get.assert_called_once_with("run-123")

    def test_fail_run_existing(self, run_service, mock_repo):
        run = Run(id="run-123", started_at=datetime.datetime.now())
        mock_repo.get.return_value = run
        mock_repo.update.side_effect = lambda x: x

        run_service.fail_run("run-123", "Something went wrong")

        assert run.status == "failed"
        assert run.last_error_message == "Something went wrong"
        assert run.completed_at is not None
        mock_repo.update.assert_called_once_with(run)

    def test_fail_run_new(self, run_service, mock_repo):
        mock_repo.get.return_value = None
        mock_repo.add.side_effect = lambda x: x

        run = run_service.fail_run("run-123", "Initial failure")

        assert run.id == "run-123"
        assert run.status == "failed"
        mock_repo.add.assert_called_once()

    def test_complete_run(self, run_service, mock_repo):
        run = Run(id="run-123", started_at=datetime.datetime.now())
        mock_repo.get.return_value = run
        mock_repo.update.side_effect = lambda x: x

        run_service.complete_run("run-123")

        assert run.status == "success"
        assert run.completed_at is not None
        mock_repo.update.assert_called_once_with(run)

    def test_complete_run_not_found(self, run_service, mock_repo):
        mock_repo.get.return_value = None

        with pytest.raises(ValueError, match="Run run-123 not found"):
            run_service.complete_run("run-123")
