from datetime import datetime
from unittest.mock import Mock

import pytest

from core.entities.listing import Listing
from core.repositories.listing_repository import ListingRepository
from core.services.listing_service import ListingService


@pytest.fixture
def mock_repo():
    return Mock(spec=ListingRepository)


@pytest.fixture
def service(mock_repo):
    return ListingService(repo=mock_repo)


class TestCreateListing:
    """Tests for the create_listing static method."""

    def test_create_listing_from_dict(self):
        """Test creating a listing from a dictionary."""
        data = {
            "id": "listing123",
            "url": "https://example.com/listing123",
            "title": "Test Car",
            "price": "25,000 KM",
        }
        listing = ListingService.create_listing(data)

        assert isinstance(listing, Listing)
        assert listing.id == "listing123"
        assert listing.url == "https://example.com/listing123"
        assert listing.title == "Test Car"
        assert listing.price == "25,000 KM"

    def test_create_listing_with_optional_fields(self):
        """Test creating a listing with optional fields."""
        data = {
            "id": "listing456",
            "url": "https://example.com/listing456",
            "title": "Another Car",
            "price": "30,000 KM",
            "visited_at": "2025-12-10T10:00:00",
            "run_id": "run_001",
        }
        listing = ListingService.create_listing(data)

        assert listing.id == "listing456"
        assert listing.run_id == "run_001"
        assert isinstance(listing.visited_at, datetime)


class TestInsertListing:
    """Tests for the insert_listing method."""

    def test_insert_listing_success(self, service, mock_repo):
        """Test successfully inserting a listing."""
        listing = Listing(
            id="listing789",
            url="https://example.com/listing789",
            title="New Car",
            price="20,000 KM",
        )
        mock_repo.add.return_value = listing
        result = service.insert_listing(listing)

        mock_repo.add.assert_called_once_with(listing)
        assert result == listing

    def test_insert_listing_calls_repo(self, service, mock_repo):
        """Test that insert_listing delegates to repository."""
        listing = Listing(
            id="listing999",
            url="https://example.com/listing999",
            title="Test Vehicle",
            price="35,000 KM",
        )
        service.insert_listing(listing)

        mock_repo.add.assert_called_once_with(listing)


class TestFindLatest:
    """Tests for the find_latest method."""

    def test_find_latest_existing_listing(self, service, mock_repo):
        """Test finding the latest version of an existing listing."""
        listing = Listing(
            id="listing111",
            url="https://example.com/listing111",
            title="Latest Car",
            price="40,000 KM",
        )
        mock_repo.find_latest.return_value = listing
        result = service.find_latest("listing111")

        mock_repo.find_latest.assert_called_once_with("listing111")
        assert result == listing

    def test_find_latest_nonexistent_listing(self, service, mock_repo):
        """Test finding a listing that doesn't exist."""
        mock_repo.find_latest.return_value = None
        result = service.find_latest("nonexistent")

        mock_repo.find_latest.assert_called_once_with("nonexistent")
        assert result is None


class TestSearchLastIngestedListings:
    """Tests for the search_last_ingested_listings method."""

    def test_search_last_ingested_listings_with_results(self, service, mock_repo):
        """Test searching for last ingested listings with results."""
        run_id = "run_123"
        listings = [
            Listing(id="l1", url="url1", title="Car 1", price="10,000 KM", run_id=run_id),
            Listing(id="l2", url="url2", title="Car 2", price="15,000 KM", run_id=run_id),
        ]

        mock_repo.find_latest_run.return_value = run_id
        mock_repo.find_without_vehicle_by_run_id.return_value = listings

        result = service.search_last_ingested_listings()

        mock_repo.find_latest_run.assert_called_once()
        mock_repo.find_without_vehicle_by_run_id.assert_called_once_with(run_id)
        assert result == listings
        assert len(result) == 2

    def test_search_last_ingested_listings_no_run(self, service, mock_repo):
        """Test searching when no run exists."""
        mock_repo.find_latest_run.return_value = None
        mock_repo.find_without_vehicle_by_run_id.return_value = []

        result = service.search_last_ingested_listings()

        mock_repo.find_latest_run.assert_called_once()
        mock_repo.find_without_vehicle_by_run_id.assert_called_once_with(None)
        assert result == []

    def test_search_last_ingested_listings_empty_results(self, service, mock_repo):
        """Test searching when run exists but no listings found."""
        run_id = "run_456"
        mock_repo.find_latest_run.return_value = run_id
        mock_repo.find_without_vehicle_by_run_id.return_value = []

        result = service.search_last_ingested_listings()

        mock_repo.find_latest_run.assert_called_once()
        mock_repo.find_without_vehicle_by_run_id.assert_called_once_with(run_id)
        assert result == []
