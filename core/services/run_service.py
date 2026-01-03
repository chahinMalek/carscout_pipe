import datetime

from core.entities.run import Run
from core.repositories.run_repository import RunRepository


class RunService:
    def __init__(self, repo: RunRepository):
        self.repo = repo

    def start_run(self, run_id: str) -> Run:
        """Creates and starts a new run."""
        existing = self.repo.get(run_id)
        if existing:
            return existing

        run = Run(id=run_id, started_at=datetime.datetime.now())
        return self.repo.add(run)

    def get_run(self, run_id: str) -> Run | None:
        return self.repo.get(run_id)

    def update_metrics(
        self, run_id: str, num_listings: int = 0, num_vehicles: int = 0, num_errors: int = 0
    ) -> Run:
        """Updates the metrics of a run."""
        run = self.repo.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        # Accumulate metrics
        run.listings_scraped += num_listings
        run.vehicles_scraped += num_vehicles
        run.errors_count += num_errors

        return self.repo.update(run)

    def fail_run(self, run_id: str, error_message: str) -> Run:
        """Marks a run as failed."""
        run = self.repo.get(run_id)
        if not run:
            # create if it not exists to at least record the failure
            run = Run(id=run_id, started_at=datetime.datetime.now())
            run.fail(error_message)
            return self.repo.add(run)

        run.fail(error_message)
        return self.repo.update(run)

    def complete_run(self, run_id: str) -> Run:
        """Marks a run as completed successfully."""
        run = self.repo.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.success()
        return self.repo.update(run)
