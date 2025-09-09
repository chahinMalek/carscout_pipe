from typing import List, Optional

from sqlalchemy import text

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.data_models.vehicles import Vehicle
from src.carscout_pipe.infra.db.connection import db_manager
from src.carscout_pipe.infra.db.repositories import ListingRepository
from src.carscout_pipe.infra.db.repositories.vehicles_repository import VehicleRepository
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
    
    # Vehicle operations
    def store_vehicles(
        self, 
        vehicles: List[Vehicle], 
        run_id: Optional[str] = None
    ) -> int:
        """Store vehicles in the database and return count of inserted vehicles."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            count = vehicle_repo.store_vehicles(vehicles, run_id)
            logger.info(f"Stored {count} vehicles in database.")
            return count
    
    def store_vehicle(
        self, 
        vehicle: Vehicle, 
        run_id: Optional[str] = None
    ) -> bool:
        """Store a single vehicle in the database."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            result = vehicle_repo.create_vehicle(vehicle, run_id)
            if result:
                logger.info(f"Stored vehicle for listing_id: {vehicle.listing_id}")
                return True
            return False
    
    def vehicle_exists_by_listing_id(self, listing_id: str) -> bool:
        """Check if a vehicle exists for the given listing_id."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            return vehicle_repo.vehicle_exists_by_listing_id(listing_id)
    
    def vehicle_exists_by_url(self, url: str) -> bool:
        """Check if a vehicle exists for the given URL."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            return vehicle_repo.vehicle_exists_by_url(url)
    
    def get_listings_without_vehicles(self, run_id: str) -> List[Listing]:
        """Get listings that don't have corresponding vehicle records."""
        with self.db_manager.get_session() as session:
            query = text("""
                WITH latest_listings AS (
                    SELECT
                        l.listing_id,
                        l.url,
                        l.title,
                        l.price,
                        l.scraped_at,
                        ROW_NUMBER() OVER (PARTITION BY l.listing_id ORDER BY l.scraped_at DESC) as rn
                    FROM listings l 
                    WHERE l.run_id = :run_id
                )
                SELECT ll.listing_id, ll.url, ll.title, ll.price
                FROM latest_listings ll
                LEFT JOIN vehicles v ON ll.listing_id = v.listing_id 
                WHERE ll.rn = 1 AND v.listing_id IS NULL
            """)
            result = session.execute(query, {"run_id": run_id})
            cols = list(result.keys())
            results = [Listing(**dict(zip(cols, row))) for row in result.fetchall()]
            return results

# Global database service instance
db_service = DatabaseService()
