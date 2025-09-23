from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.infra.db.models import ListingModel


class ListingRepository:
    """Repository for listing data access operations."""

    def __init__(self, session: Session):
        self.session = session

    def create_listing(self, listing: Listing, run_id: str) -> ListingModel:
        """Create a new listing in the database."""
        listing_model = ListingModel(**{**listing.__dict__, "run_id": run_id})
        self.session.add(listing_model)
        return listing_model

    def get_listing_by_url(self, url: str) -> Optional[ListingModel]:
        """Get a listing by its URL."""
        return self.session.query(ListingModel).filter(ListingModel.url == url).first()

    def get_listings_by_run_id(self, run_id: str) -> List[ListingModel]:
        """Get all listings for a specific scraping run."""
        return (
            self.session.query(ListingModel).filter(ListingModel.run_id == run_id).all()
        )

    def get_all_listings(self, limit: Optional[int] = None) -> List[ListingModel]:
        """Get all listings with optional limit."""
        query = self.session.query(ListingModel).order_by(
            ListingModel.scraped_at.desc()
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def bulk_create_listings(
        self, listings: List[Listing], run_id: Optional[str] = None
    ) -> List[ListingModel]:
        """Create multiple listings in the database and return count of inserted records.

        Note: This allows duplicates as the listings table is a historical record
        that captures all versions of listings over time (e.g., price changes).
        """
        if not listings:
            return 0

        # Prepare bulk insert data
        bulk_data = []

        for listing in listings:
            bulk_data.append(
                {
                    "listing_id": listing.listing_id,
                    "url": listing.url,
                    "title": listing.title,
                    "price": listing.price,
                    "run_id": run_id,
                    "scraped_at": datetime.now(),
                }
            )

        # Perform bulk insert
        self.session.bulk_insert_mappings(ListingModel, bulk_data)
        return len(listings)

    def count_listings(self) -> int:
        """Get total count of listings."""
        return self.session.query(ListingModel).count()

    def count_listings_by_run_id(self, run_id: str) -> int:
        """Get count of listings for a specific run."""
        return (
            self.session.query(ListingModel)
            .filter(ListingModel.run_id == run_id)
            .count()
        )
