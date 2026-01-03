from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from infra.db.models.base import Base


class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    listings_scraped = Column(Integer, default=0)
    vehicles_scraped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    last_error_message = Column(String, nullable=True)
