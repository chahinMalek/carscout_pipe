from core.repositories.vehicle_repository import VehicleRepository
from core.entities.vehicle import Vehicle
from infra.db.models.vehicle import VehicleModel
from infra.db.service import DatabaseService


class SqlAlchemyVehicleRepository(VehicleRepository):

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def add(self, vehicle: Vehicle) -> Vehicle:
        pass

    def get(self, id: int) -> Vehicle | None:
        pass
