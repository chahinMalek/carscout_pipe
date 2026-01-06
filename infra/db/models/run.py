from datetime import UTC, datetime

from sqlalchemy import Column, Integer, String

from core.entities.run import RunStatus
from infra.db.models.base import Base, SQLiteSafeDateTime


class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)
    started_at = Column(SQLiteSafeDateTime, default=datetime.now(UTC))
    completed_at = Column(SQLiteSafeDateTime, nullable=True)
    status = Column(String, default=RunStatus.RUNNING.value)
    listings_scraped = Column(Integer, default=0)
    vehicles_scraped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    last_error_message = Column(String, nullable=True)
