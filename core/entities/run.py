import datetime
from dataclasses import dataclass
from enum import Enum


class RunStatus(str, Enum):
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"

    @classmethod
    def all_statuses(cls):
        return [st.value for st in cls]


@dataclass
class Run:
    id: str
    started_at: datetime.datetime
    status: RunStatus = RunStatus.RUNNING
    completed_at: datetime.datetime | None = None
    listings_scraped: int = 0
    vehicles_scraped: int = 0
    errors_count: int = 0
    last_error_message: str | None = None

    def fail(self, error_message: str):
        self.status = RunStatus.FAILED
        self.completed_at = datetime.datetime.now()
        self.last_error_message = error_message

    def success(self):
        self.status = RunStatus.SUCCESS
        self.completed_at = datetime.datetime.now()
