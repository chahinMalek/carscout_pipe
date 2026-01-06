from dataclasses import asdict

from sqlalchemy import inspect, select

from core.entities.vehicle import Vehicle
from core.repositories.vehicle_repository import VehicleRepository
from infra.db.models.vehicle import VehicleModel
from infra.db.service import DatabaseService


class SqlAlchemyVehicleRepository(VehicleRepository):
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def _convert_orm_to_entity(self, orm: VehicleModel) -> Vehicle:
        # use field introspection to map fields
        mapper = inspect(VehicleModel)
        column_names = {col.key for col in mapper.columns}
        data = {col_name: getattr(orm, col_name) for col_name in column_names}
        data["id"] = data.pop("listing_id", None)
        return Vehicle.from_dict(data)

    def _convert_entity_to_orm(self, entity: Vehicle) -> VehicleModel:
        data = asdict(entity)
        data["listing_id"] = data.pop("id", None)
        return VehicleModel(**data)

    def add(self, vehicle: Vehicle) -> Vehicle:
        with self.db_service.create_session() as session:
            record = self._convert_entity_to_orm(vehicle)
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._convert_orm_to_entity(record)

    def get(self, id: str) -> Vehicle | None:
        with self.db_service.create_session() as session:
            query = select(VehicleModel).filter_by(listing_id=id)
            result = session.execute(query).scalars().first()
            return self._convert_orm_to_entity(result) if result else None

    def list_all(self, limit: int = 1000) -> list[Vehicle]:
        with self.db_service.create_session() as session:
            query = select(VehicleModel).limit(limit)
            result = session.execute(query).scalars().all()
            return [self._convert_orm_to_entity(orm) for orm in result]
