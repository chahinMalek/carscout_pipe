from core.repositories.listing_repository import ListingRepository
from core.entities.listing import Listing
from infra.db.models.listing import ListingModel
from infra.db.service import DatabaseService


class SqlAlchemyListingRepository(ListingRepository):

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def add(self, listing: Listing) -> Listing:
        with self.db_service.create_session() as session:
            record = ListingModel(
                listing_id=listing.id,
                url=listing.url,
                title=listing.title,
                price=listing.price,
                visited_at=listing.visited_at,
                run_id=listing.run_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return Listing(
                id=record.listing_id,
                url=record.url,
                title=record.title,
                price=record.price,
                visited_at=record.visited_at,
                run_id=record.run_id,
            )
