from core.repositories.vehicle_repository import VehicleRepository
from core.entities.vehicle import Vehicle
from infra.db.models.vehicle import VehicleModel
from infra.db.service import DatabaseService


class SqlAlchemyVehicleRepository(VehicleRepository):

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    # def _convert_orm_to_entity(self, orm: VehicleModel):
    #     return Vehicle(
    #         ...
    #     )
    #
    # def _convert_entity_to_orm(self, orm: Vehicle):
    #     return VehicleModel(
    #         ...
    #     )
    #
    # def add(self, vehicle: Vehicle) -> Vehicle:
    #     with self.db_service.create_session() as session:
    #         record = self._convert_entity_to_orm(vehicle)
    #         session.add(record)
    #         session.commit()
    #         session.refresh(record)
    #         return self._convert_orm_to_entity(record)
    #
    # def get(self, id: int) -> Vehicle | None:
    #     pass
