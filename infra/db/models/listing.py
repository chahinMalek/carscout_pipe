from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from infra.db.models.base import Base


class ListingModel(Base):
    __tablename__ = "listings"

    # primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # fields
    listing_id = Column(String, ForeignKey("vehicles.listing_id"), index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)
    visited_at = Column(DateTime, nullable=True)
    run_id = Column(String, nullable=True)

    # relationships
    vehicle = relationship("VehicleModel", back_populates="listings")
