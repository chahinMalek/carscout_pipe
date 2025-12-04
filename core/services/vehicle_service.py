import datetime

from core.entities.vehicle import Vehicle
from core.repositories.vehicle_repository import VehicleRepository


class VehicleService:

    def __init__(self, repo: VehicleRepository):
        self.repo = repo

    @staticmethod
    def create_listing(data: dict) -> Vehicle:
        return Vehicle.from_dict(data)

    def add_vehicle(self, vehicle: Vehicle) -> Vehicle:
        pass

    def update_vehicle(self, vehicle: Vehicle) -> Vehicle:
        pass

    def get_vehicle(self, id: str) -> Vehicle:
        pass
