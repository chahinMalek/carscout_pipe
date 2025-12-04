from datetime import datetime, timedelta

import pytest

from core.entities.listing import Listing
from core.services.listing_service import ListingService


class FakeListingRepository:
    """In-memory implementation of ListingRepository for testing."""

    def __init__(self):
        self._storage = {}  # listing_id -> Listing

    def add_or_update(self, listing: Listing) -> Listing:
        # emulate DB-assigned created_at if not set
        if listing.created_at is None:
            listing.created_at = datetime.utcnow()
        self._storage[listing.listing_id] = listing
        return listing

    def get(self, listing_id: str):
        return self._storage.get(listing_id)

    def update(self, listing: Listing) -> Listing:
        self._storage[listing.listing_id] = listing
        return listing

    def query_by_created_range(self, start: datetime, end: datetime):
        return [
            l for l in self._storage.values()
            if l.created_at is not None and start <= l.created_at <= end
        ]


@pytest.fixture
def service():
    repo = FakeListingRepository()
    return ListingService(listing_repo=repo)


def test_create_listing_from_raw_ok(service):
    raw = {"listing_id": " A123 ", "url": " https://example.com ", "price": "15000"}
    listing = service.create_listing_from_raw(raw)

    assert listing.listing_id == "A123"
    assert listing.url == "https://example.com"
    assert listing.price == 15000.0
    assert listing.created_at is not None


def test_update_listing(service):
    # create first
    raw = {"listing_id": "A1", "url": "https://example.com", "price": "15000"}
    created = service.create_listing_from_raw(raw)

    updated = service.update_listing("A1", {"price": 20000, "url": " https://new.com "})
    assert updated is not None
    assert updated.price == 20000
    assert updated.url == "https://new.com"


def test_query_listings_by_time(service):
    now = datetime.utcnow()
    earlier = now - timedelta(days=1)
    later = now + timedelta(days=1)

    raw1 = {"listing_id": "A1", "url": "https://example.com/A1", "price": "15000"}
    raw2 = {"listing_id": "B2", "url": "https://example.com/B2", "price": "18000"}

    l1 = service.create_listing_from_raw(raw1)
    l2 = service.create_listing_from_raw(raw2)

    # manually tweak timestamps for predictability
    l1.created_at = now - timedelta(hours=12)
    l2.created_at = now + timedelta(hours=12)

    service.repo.update(l1)
    service.repo.update(l2)

    results = service.query_listings_by_time(earlier, now)
    ids = {l.listing_id for l in results}
    assert "A1" in ids
    assert "B2" not in ids
