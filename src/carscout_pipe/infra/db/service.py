from typing import List, Optional

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.infra.db.connection import db_manager
from src.carscout_pipe.infra.db.repositories import ListingRepository
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """Service layer for database operations."""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def initialize_database(self):
        """Initialize the database by creating all tables."""
        logger.info("Initializing database tables...")
        self.db_manager.create_tables()
        logger.info("Database tables created successfully.")
    
    def store_listings(
        self, 
        listings: List[Listing], 
        run_id: Optional[str] = None
    ) -> int:
        """Store listings in the database and return count of inserted listings."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            count = listing_repo.bulk_create_listings(listings, run_id)
            logger.info(f"Stored {count} listings in database.")
            return count
    
    def get_listings_by_run_id(self, run_id: str) -> List[dict]:
        """Get all listings for a specific scraping run."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            listings = listing_repo.get_listings_by_run_id(run_id)
            return [
                {
                    "id": listing.id,
                    "url": listing.url,
                    "title": listing.title,
                    "price": listing.price,
                    "scraped_at": listing.scraped_at,
                    "run_id": listing.run_id
                }
                for listing in listings
            ]
    
    def get_all_listings(self, limit: Optional[int] = None) -> List[dict]:
        """Get all listings with optional limit."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            listings = listing_repo.get_all_listings(limit)
            return [
                {
                    "id": listing.id,
                    "url": listing.url,
                    "title": listing.title,
                    "price": listing.price,
                    "scraped_at": listing.scraped_at,
                    "run_id": listing.run_id
                }
                for listing in listings
            ]
    
    def count_listings(self) -> int:
        """Get total count of listings."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            return listing_repo.count_listings()
    
    def count_listings_by_run_id(self, run_id: str) -> int:
        """Get count of listings for a specific run."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            return listing_repo.count_listings_by_run_id(run_id)


# Global database service instance
db_service = DatabaseService()
