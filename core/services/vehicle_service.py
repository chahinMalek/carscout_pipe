from core.entities.vehicle import Vehicle
from core.repositories.vehicle_repository import VehicleRepository


class VehicleService:
    def __init__(self, repo: VehicleRepository):
        self.repo = repo

    @staticmethod
    def create_listing(data: dict) -> Vehicle:
        return Vehicle.from_dict(data)

    def insert_vehicle(self, vehicle: Vehicle) -> Vehicle:
        return self.repo.add(vehicle)

    def vehicle_exists(self, id: str) -> bool:
        return self.repo.get(id) is not None

    def get_vehicle(self, id: str) -> Vehicle | None:
        return self.repo.get(id)
