import datetime
from dataclasses import dataclass


@dataclass
class Run:
    id: str
    started_at: datetime.datetime
    status: str = "running"
    completed_at: datetime.datetime | None = None
    listings_scraped: int = 0
    vehicles_scraped: int = 0
    errors_count: int = 0
    last_error_message: str | None = None

    def fail(self, error_message: str):
        self.status = "failed"
        self.completed_at = datetime.datetime.now()
        self.last_error_message = error_message

    def success(self):
        self.status = "success"
        self.completed_at = datetime.datetime.now()
