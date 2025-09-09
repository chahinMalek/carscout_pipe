from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.carscout_pipe.core.data_models.vehicles import Vehicle
from src.carscout_pipe.infra.db.models.vehicles import VehicleModel
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)


class VehicleRepository:
    """Repository for vehicle data operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_vehicle(self, vehicle: Vehicle, run_id: str) -> VehicleModel:
        """Create a new vehicle record in the database."""
        vehicle_model = VehicleModel(**{**vehicle.__dict__, "run_id": run_id, "scraped_at": datetime.now()})
        self.session.add(vehicle_model)
        return vehicle_model
    
    def get_vehicle_by_listing_id(self, listing_id: str) -> Optional[VehicleModel]:
        """Get a vehicle by listing_id."""
        return self.session.query(VehicleModel).filter(VehicleModel.listing_id == listing_id).first()
    
    def get_vehicle_by_url(self, url: str) -> Optional[VehicleModel]:
        """Get a vehicle by URL."""
        return self.session.query(VehicleModel).filter(VehicleModel.url == url).first()

    def vehicle_exists_by_listing_id(self, listing_id: str) -> bool:
        """Check if a vehicle exists by listing_id."""
        try:
            vehicle = self.get_vehicle_by_listing_id(listing_id)
            return vehicle is not None
        except Exception as e:
            logger.error(f"Failed to check vehicle existence by listing_id {listing_id}: {e}")
            return False
    
    def vehicle_exists_by_url(self, url: str) -> bool:
        """Check if a vehicle exists by URL."""
        try:
            vehicle = self.get_vehicle_by_url(url)
            return vehicle is not None
        except Exception as e:
            logger.error(f"Failed to check vehicle existence by URL {url}: {e}")
            return False
    
    def store_vehicles(self, vehicles: List[Vehicle], run_id: str = None) -> int:
        """Store multiple vehicles and return the number of successfully inserted records."""
        inserted_count = 0
        
        for vehicle in vehicles:
            if self.create_vehicle(vehicle, run_id):
                inserted_count += 1
        
        return inserted_count
    
    def get_listings_without_vehicles(self) -> List[dict]:
        """Get listings that don't have corresponding vehicle records."""
        try:
            # This would join with the listings table to find listings without vehicles
            # For now, returning empty list - will need to implement when integrating with listings
            return []
        except Exception as e:
            logger.error(f"Failed to get listings without vehicles: {e}")
            return []
