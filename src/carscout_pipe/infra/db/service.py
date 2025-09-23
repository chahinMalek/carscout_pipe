from datetime import datetime
from typing import List, Optional

from sqlalchemy import text

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.data_models.vehicles import Vehicle
from src.carscout_pipe.infra.db.connection import db_manager
from src.carscout_pipe.infra.db.repositories import ListingRepository
from src.carscout_pipe.infra.db.repositories.vehicles_repository import (
    VehicleRepository,
)
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
        self, listings: List[Listing], run_id: Optional[str] = None
    ) -> int:
        """Store listings in the database and return count of inserted listings."""
        with self.db_manager.get_session() as session:
            listing_repo = ListingRepository(session)
            count = listing_repo.bulk_create_listings(listings, run_id)
            logger.info(f"Stored {count} listings in database.")
            return count

    def store_vehicle(self, vehicle: Vehicle, run_id: Optional[str] = None) -> bool:
        """Store a single vehicle in the database."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            result = vehicle_repo.create_vehicle(vehicle, run_id)
            if result:
                logger.info(f"Stored vehicle for listing_id: {vehicle.listing_id}")
                return True
            return False

    def get_listings_without_vehicles(self, run_id: str) -> List[Listing]:
        """Get listings that don't have corresponding vehicle records."""
        with self.db_manager.get_session() as session:
            query = text("""
                WITH run_listings AS (
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
                SELECT rl.listing_id, rl.url, rl.title, rl.price
                FROM run_listings rl
                LEFT JOIN vehicles v ON rl.listing_id = v.listing_id 
                WHERE rl.rn = 1 AND v.listing_id IS NULL
            """)
            result = session.execute(query, {"run_id": run_id})
            cols = list(result.keys())
            results = [Listing(**dict(zip(cols, row))) for row in result.fetchall()]
            return results

    def get_vehicles_with_null_attributes(
        self, keep_after: Optional[datetime] = None
    ) -> List[dict]:
        """Get vehicles that have null brand or model values."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            vehicles = vehicle_repo.get_vehicles_with_null_attributes(
                keep_after=keep_after
            )
            return [
                {
                    "listing_id": vehicle.listing_id,
                    "url": vehicle.url,
                    "title": vehicle.title,
                    "price": vehicle.price,
                    "brand": vehicle.brand,
                    "model": vehicle.model,
                }
                for vehicle in vehicles
            ]

    def update_vehicle(self, listing_id: str, vehicle: Vehicle) -> bool:
        """Update an existing vehicle record."""
        with self.db_manager.get_session() as session:
            vehicle_repo = VehicleRepository(session)
            return vehicle_repo.update_vehicle(listing_id, vehicle)


# Global database service instance
db_service = DatabaseService()
