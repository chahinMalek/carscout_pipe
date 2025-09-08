from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ListingModel(Base):
    __tablename__ = "listings"

    # primary key    
    id = Column(Integer, primary_key=True, autoincrement=True)

    # fields related to the actual listing
    listing_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(String, nullable=True)
    
    # scraping metadata
    scraped_at = Column(DateTime, default=datetime.now(), nullable=False)
    run_id = Column(String, nullable=True)
