import datetime
from dataclasses import asdict

from sqlalchemy import Integer, cast, func, inspect, select

from core.entities.vehicle import Vehicle
from core.repositories.vehicle_repository import VehicleRepository
from infra.db.models.listing import ListingModel
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

    def search(
        self,
        listing_id: str | None = None,
        title: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_date: datetime.datetime | None = None,
        max_date: datetime.datetime | None = None,
        brand: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Vehicle], int]:
        with self.db_service.create_session() as session:
            query = select(VehicleModel)

            # prepare filters
            if listing_id:
                query = query.filter(VehicleModel.listing_id.like(f"%{listing_id}%"))
            if title:
                query = query.filter(VehicleModel.title.like(f"%{title}%"))
            if brand:
                query = query.filter(VehicleModel.brand == brand)
            if min_date:
                query = query.filter(VehicleModel.last_visited_at >= min_date)
            if max_date:
                query = query.filter(VehicleModel.last_visited_at <= max_date)

            if min_price is not None or max_price is not None:
                price_clean = func.strip(
                    func.replace(func.replace(VehicleModel.price, "KM", ""), ".", "")
                )
                price_int = cast(price_clean, Integer)

                query = query.filter(VehicleModel.price.is_not(None))
                query = query.filter(VehicleModel.price != "")
                query = query.filter(VehicleModel.price != "Na upit")

                if min_price is not None:
                    query = query.filter(price_int >= min_price)
                if max_price is not None:
                    query = query.filter(price_int <= max_price)

            # count results
            count_query = select(func.count()).select_from(query.subquery())
            total_count = session.execute(count_query).scalar() or 0

            # pagination
            query = query.order_by(VehicleModel.last_visited_at.desc()).offset(offset).limit(limit)
            result = session.execute(query).scalars().all()

            entities = [self._convert_orm_to_entity(orm) for orm in result]
            return entities, total_count

    def get_unique_brands(self) -> list[str]:
        with self.db_service.create_session() as session:
            query = select(VehicleModel.brand).distinct().order_by(VehicleModel.brand.asc())
            result = session.execute(query).scalars().all()
            return [str(r) for r in result if r is not None]

    def get_new_vehicles_per_run(self, limit: int = 50) -> list[dict]:
        with self.db_service.create_session() as session:
            # subquery to find the earliest visited_at and its run_id for each listing_id
            first_occurrence = (
                select(
                    ListingModel.listing_id,
                    ListingModel.run_id,
                    ListingModel.visited_at,
                )
                .distinct(ListingModel.listing_id)
                .order_by(ListingModel.listing_id, ListingModel.visited_at.asc())
                .subquery()
            )

            # only include listing_ids that have vehicles
            vehicles_with_first_run = (
                select(
                    first_occurrence.c.run_id,
                    first_occurrence.c.visited_at,
                )
                .select_from(first_occurrence)
                .join(
                    VehicleModel,
                    VehicleModel.listing_id == first_occurrence.c.listing_id,
                )
                .subquery()
            )

            # group by run_id and count
            query = (
                select(
                    vehicles_with_first_run.c.run_id,
                    func.min(vehicles_with_first_run.c.visited_at).label("run_started_at"),
                    func.count().label("new_vehicle_count"),
                )
                .group_by(vehicles_with_first_run.c.run_id)
                .order_by(func.min(vehicles_with_first_run.c.visited_at).desc())
                .limit(limit)
            )
            result = session.execute(query).all()

            return [
                {
                    "run_id": row.run_id,
                    "run_started_at": row.run_started_at,
                    "new_vehicle_count": row.new_vehicle_count,
                }
                for row in result
            ]
