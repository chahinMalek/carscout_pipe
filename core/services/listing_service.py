import datetime

from core.entities.listing import Listing
from core.repositories.listing_repository import ListingRepository


class ListingService:

    def __init__(self, repo: ListingRepository):
        self.repo = repo

    @staticmethod
    def create_listing(data: dict) -> Listing:
        return Listing.from_dict(data)

    def insert_listing(self, listing: Listing) -> Listing:
        return self.repo.add(listing)

    def find_latest(self, listing_id: str) -> Listing | None:
        return self.repo.find_latest(listing_id)

    def search_last_ingested_listings(self) -> list[Listing]:
        latest_run_id = self.repo.find_latest_run()
        return self.repo.search_with_run_id(latest_run_id)
