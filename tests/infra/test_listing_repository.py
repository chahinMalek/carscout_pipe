from datetime import UTC, datetime, timedelta

import pytest

from core.entities.listing import Listing
from infra.db.models.listing import ListingModel
from infra.db.models.vehicle import VehicleModel
from infra.db.repositories.listings import SqlAlchemyListingRepository


@pytest.mark.integration
class TestSqlAlchemyListingRepository:
    @pytest.fixture
    def repo(self, in_memory_db):
        return SqlAlchemyListingRepository(in_memory_db)

    @pytest.fixture
    def sample_listing(self):
        return Listing(
            id="listing-001",
            url="https://olx.ba/listing-001",
            title="Toyota Corolla 2020",
            price="25000 KM",
            visited_at=datetime.now(UTC),
            run_id="run-001",
        )

    def test_add_listing(self, repo, sample_listing, in_memory_db):
        result = repo.add(sample_listing)

        # check results match
        assert result.id == sample_listing.id
        assert result.url == sample_listing.url
        assert result.title == sample_listing.title
        assert result.price == sample_listing.price
        assert result.run_id == sample_listing.run_id

        # check result is stored in the db
        with in_memory_db.create_session() as session:
            result = session.query(ListingModel).filter_by(listing_id=sample_listing.id).first()
            assert result is not None
            assert result.url == sample_listing.url

    def test_exists(self, repo, sample_listing):
        repo.add(sample_listing)

        assert repo.exists(sample_listing.id) is True
        assert repo.exists("non-existent-id") is False

    def test_find_latest(self, repo):
        now = datetime.now(UTC)

        older_listing = Listing(
            id="listing-001",
            url="https://olx.ba/listing-001",
            title="Old Title",
            price="20000 KM",
            visited_at=now - timedelta(hours=2),
            run_id="run-001",
        )
        repo.add(older_listing)

        newer_listing = Listing(
            id="listing-001",
            url="https://olx.ba/listing-001",
            title="New Title",
            price="25000 KM",
            visited_at=now,
            run_id="run-002",
        )
        repo.add(newer_listing)

        # returns the newer listing
        result = repo.find_latest("listing-001")

        assert result is not None
        assert result.title == "New Title"
        assert result.price == "25000 KM"
        assert result.run_id == "run-002"

        # returns None for non-existing listing
        result = repo.find_latest("non-existent-id")
        assert result is None

    def test_find_all(self, repo):
        for i in range(3):
            listing = Listing(
                id="listing-001",
                url="https://olx.ba/listing-001",
                title=f"Version {i}",
                price=f"{20000 + i * 1000} KM",
                visited_at=datetime.now(UTC),
                run_id=f"run-{i:03d}",
            )
            repo.add(listing)

        results = repo.find_all("listing-001")

        # returns the same number of listings as ones added and their id is the same
        assert len(results) == 3
        assert all(r.id == "listing-001" for r in results)

        # returns empty list for non-existing listing
        results = repo.find_all("non-existent-id")
        assert results == []

    def test_find_latest_run(self, repo):
        now = datetime.now(UTC)

        listing1 = Listing(
            id="listing-001",
            url="https://olx.ba/listing-001",
            title="First",
            price="20000 KM",
            visited_at=now - timedelta(hours=2),
            run_id="run-001",
        )
        repo.add(listing1)

        listing2 = Listing(
            id="listing-002",
            url="https://olx.ba/listing-002",
            title="Second",
            price="30000 KM",
            visited_at=now,
            run_id="run-002",
        )
        repo.add(listing2)

        # returns the most recently added run_id
        result = repo.find_latest_run()
        assert result == "run-002"

    def test_find_without_vehicle_by_run_id(self, repo, in_memory_db):
        # listing without vehicle
        listing1 = Listing(
            id="listing-001",
            url="https://olx.ba/listing-001",
            title="Without Vehicle",
            price="20000 KM",
            visited_at=datetime.now(UTC),
            run_id="run-001",
        )
        repo.add(listing1)

        # listing with vehicle
        listing2 = Listing(
            id="listing-002",
            url="https://olx.ba/listing-002",
            title="With Vehicle",
            price="30000 KM",
            visited_at=datetime.now(UTC),
            run_id="run-001",
        )
        repo.add(listing2)

        # vehicle for listing2
        with in_memory_db.create_session() as session:
            vehicle = VehicleModel(
                listing_id="listing-002",
                url="https://olx.ba/listing-002",
                title="With Vehicle",
                price="30000 KM",
                brand="Toyota",
                model="Corolla",
                last_visited_at=datetime.now(UTC),
            )
            session.add(vehicle)
            session.commit()

        results = repo.find_without_vehicle_by_run_id("run-001")

        assert len(results) == 1
        assert results[0].id == "listing-001"

    def test_search_with_run_id(self, repo):
        # Add listings with different run_ids
        for i in range(3):
            listing = Listing(
                id=f"listing-{i:03d}",
                url=f"https://olx.ba/listing-{i:03d}",
                title=f"Listing {i}",
                price=f"{20000 + i * 1000} KM",
                visited_at=datetime.now(UTC),
                run_id="run-001",
            )
            repo.add(listing)

        # Add listing with different run_id
        other_listing = Listing(
            id="listing-999",
            url="https://olx.ba/listing-999",
            title="Other",
            price="50000 KM",
            visited_at=datetime.now(UTC),
            run_id="run-002",
        )
        repo.add(other_listing)

        # check run-001
        results = repo.search_with_run_id("run-001")
        assert len(results) == 3
        assert all(r.run_id == "run-001" for r in results)

        # check run-002
        results = repo.search_with_run_id("run-002")
        assert len(results) == 1
        assert all(r.run_id == "run-002" for r in results)

        # returns empty list for a non-existing run_id
        results = repo.search_with_run_id("unknown-run")
        assert results == []

    def test_convert_entity_to_orm_and_back(self, repo, sample_listing):
        orm = repo._convert_entity_to_orm(sample_listing)
        entity = repo._convert_orm_to_entity(orm)

        assert entity.id == sample_listing.id
        assert entity.url == sample_listing.url
        assert entity.title == sample_listing.title
        assert entity.price == sample_listing.price
        assert entity.run_id == sample_listing.run_id
