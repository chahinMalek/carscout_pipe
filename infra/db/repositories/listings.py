import datetime

from sqlalchemy import select

from core.entities.listing import Listing
from core.repositories.listing_repository import ListingRepository
from infra.db.models.listing import ListingModel
from infra.db.models.vehicle import VehicleModel
from infra.db.service import DatabaseService


class SqlAlchemyListingRepository(ListingRepository):
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def _convert_orm_to_entity(self, orm: ListingModel):
        return Listing(
            id=orm.listing_id,
            url=orm.url,
            title=orm.title,
            price=orm.price,
            visited_at=orm.visited_at,
            run_id=orm.run_id,
        )

    def _convert_entity_to_orm(self, entity: Listing):
        return ListingModel(
            listing_id=entity.id,
            url=entity.url,
            title=entity.title,
            price=entity.price,
            visited_at=entity.visited_at,
            run_id=entity.run_id,
        )

    def add(self, listing: Listing) -> Listing:
        with self.db_service.create_session() as session:
            record = self._convert_entity_to_orm(listing)
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._convert_orm_to_entity(record)

    def exists(self, id: str) -> bool:
        with self.db_service.create_session() as session:
            query = select(ListingModel).filter_by(listing_id=id)
            result = session.execute(query).scalars().first()
            return result is not None

    def find_latest(self, id: str) -> Listing | None:
        with self.db_service.create_session() as session:
            query = (
                select(ListingModel)
                .filter_by(listing_id=id)
                .order_by(ListingModel.visited_at.desc())
                .limit(1)
            )
            result = session.execute(query).scalars().first()
            if result:
                return self._convert_orm_to_entity(result)

    def find_all(self, id: str) -> list[Listing]:
        with self.db_service.create_session() as session:
            query = select(ListingModel).filter_by(listing_id=id)
            result = session.execute(query).scalars().all()
            return [self._convert_orm_to_entity(orm) for orm in result]

    def find_latest_run(self) -> str | None:
        """Returns the run_id of the most recently inserted listing record."""
        with self.db_service.create_session() as session:
            query = select(ListingModel).order_by(ListingModel.visited_at.desc()).limit(1)
            result = session.execute(query).scalars().first()
            return result.run_id if result else None

    def find_without_vehicle_by_run_id(self, run_id: str) -> list[Listing]:
        """Find all listings with the given run_id that don't have vehicle information stored."""
        with self.db_service.create_session() as session:
            query = (
                select(ListingModel)
                .outerjoin(ListingModel.vehicle)
                .filter(ListingModel.run_id == run_id)
                .filter(VehicleModel.listing_id.is_(None))
            )
            result = session.execute(query).scalars().all()
            return [self._convert_orm_to_entity(orm) for orm in result]

    def search_with_run_id(self, run_id: str) -> list[Listing]:
        """Returns a list of listings found for a given run_id."""
        with self.db_service.create_session() as session:
            query = select(ListingModel).filter_by(run_id=run_id)
            result = session.execute(query).scalars().all()
            return [self._convert_orm_to_entity(orm) for orm in result]

    def search_at(self, date: datetime.datetime) -> list[Listing]:
        raise NotImplementedError("Search by date is not yet implemented.")

    def search_between(
        self, date_from: datetime.datetime, date_to: datetime.datetime
    ) -> list[Listing]:
        raise NotImplementedError("Search by date range is not yet implemented.")
