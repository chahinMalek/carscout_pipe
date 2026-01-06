import datetime

from sqlalchemy import Integer, cast, func, select

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

    def search(
        self,
        listing_id: str | None = None,
        title: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_date: datetime.datetime | None = None,
        max_date: datetime.datetime | None = None,
        run_id: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Listing], int]:
        with self.db_service.create_session() as session:
            query = select(ListingModel)

            if listing_id:
                query = query.filter(ListingModel.listing_id.like(f"%{listing_id}%"))
            if title:
                query = query.filter(ListingModel.title.like(f"%{title}%"))
            if run_id:
                query = query.filter(ListingModel.run_id == run_id)
            if min_date:
                query = query.filter(ListingModel.visited_at >= min_date)
            if max_date:
                query = query.filter(ListingModel.visited_at <= max_date)

            if min_price is not None or max_price is not None:
                price_clean = func.strip(
                    func.replace(func.replace(ListingModel.price, "KM", ""), ".", "")
                )
                price_int = cast(price_clean, Integer)

                query = query.filter(ListingModel.price.is_not(None))
                query = query.filter(ListingModel.price != "")
                query = query.filter(ListingModel.price != "Na upit")

                if min_price is not None:
                    query = query.filter(price_int >= min_price)
                if max_price is not None:
                    query = query.filter(price_int <= max_price)

            # count results
            count_query = select(func.count()).select_from(query.subquery())
            total_count = session.execute(count_query).scalar() or 0

            # pagination
            query = query.order_by(ListingModel.visited_at.desc()).offset(offset).limit(limit)
            result = session.execute(query).scalars().all()

            entities = [self._convert_orm_to_entity(orm) for orm in result]
            return entities, total_count

    def get_unique_run_ids(self) -> list[str]:
        with self.db_service.create_session() as session:
            query = select(ListingModel.run_id).distinct().order_by(ListingModel.run_id.desc())
            result = session.execute(query).scalars().all()
            return [str(r) for r in result if r is not None]
