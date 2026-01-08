from datetime import UTC, datetime, timedelta

import pytest

from core.entities.listing import Listing
from core.entities.vehicle import Vehicle
from infra.db.models.vehicle import VehicleModel
from infra.db.repositories.listings import SqlAlchemyListingRepository
from infra.db.repositories.vehicles import SqlAlchemyVehicleRepository


@pytest.mark.integration
class TestSqlAlchemyVehicleRepository:
    @pytest.fixture
    def repo(self, in_memory_db):
        return SqlAlchemyVehicleRepository(in_memory_db)

    @pytest.fixture
    def sample_vehicle(self):
        return Vehicle(
            id="vehicle-001",
            url="https://olx.ba/vehicle-001",
            title="Toyota Corolla 2020",
            price="25000 KM",
            brand="Toyota",
            model="Corolla",
            build_year=2020,
            mileage="50000",
            fuel_type="Benzin",
            transmission="Automatik",
            engine_volume="1800",
            engine_power=140,
            last_visited_at=datetime.now(UTC),
        )

    def test_add_vehicle(self, repo, sample_vehicle, in_memory_db):
        result = repo.add(sample_vehicle)

        # check results match
        assert result.id == sample_vehicle.id
        assert result.brand == sample_vehicle.brand
        assert result.model == sample_vehicle.model
        assert result.build_year == sample_vehicle.build_year
        assert result.mileage == sample_vehicle.mileage
        assert result.fuel_type == sample_vehicle.fuel_type
        assert result.transmission == sample_vehicle.transmission

        # check result is stored in the db
        with in_memory_db.create_session() as session:
            result = session.query(VehicleModel).filter_by(listing_id=sample_vehicle.id).first()
            assert result is not None
            assert result.brand == sample_vehicle.brand
            assert result.model == sample_vehicle.model

    def test_add_vehicle_with_optional_fields(self, repo):
        vehicle = Vehicle(
            id="vehicle-minimal",
            url="https://olx.ba/vehicle-minimal",
            title="Toyota Corolla",
            price="25000 KM",
            brand="Toyota",
            model="Corolla",
            last_visited_at=datetime.now(UTC),
            build_year=None,
            mileage=None,
            fuel_type=None,
            transmission=None,
            engine_volume=None,
            engine_power=None,
        )

        result = repo.add(vehicle)

        assert result.id == "vehicle-minimal"
        assert result.brand == "Toyota"
        assert result.model == "Corolla"
        assert result.build_year is None
        assert result.mileage is None

    def test_get(self, repo, sample_vehicle):
        repo.add(sample_vehicle)

        result = repo.get(sample_vehicle.id)

        # check results match
        assert result is not None
        assert result.id == sample_vehicle.id
        assert result.brand == sample_vehicle.brand
        assert result.model == sample_vehicle.model

        # returns None for non-existing vehicle
        result = repo.get("non-existent-id")
        assert result is None

    def test_add_multiple_vehicles(self, repo):
        vehicles = []
        for i in range(3):
            vehicle = Vehicle(
                id=f"vehicle-{i:03d}",
                url=f"https://olx.ba/vehicle-{i:03d}",
                title=f"Vehicle {i}",
                price="25000 KM",
                brand=f"Brand-{i}",
                model=f"Model-{i}",
                build_year=2020 + i,
                mileage=f"{50000 + i * 10000}",
                fuel_type="Benzin",
                transmission="Automatik",
                last_visited_at=datetime.now(UTC),
            )
            vehicles.append(repo.add(vehicle))

        assert len(vehicles) == 3
        for i, vehicle in enumerate(vehicles):
            assert vehicle.id == f"vehicle-{i:03d}"
            retrieved = repo.get(vehicle.id)
            assert retrieved is not None
            assert retrieved.brand == f"Brand-{i}"

    def test_convert_entity_to_orm_and_back(self, repo, sample_vehicle):
        orm = repo._convert_entity_to_orm(sample_vehicle)
        entity = repo._convert_orm_to_entity(orm)

        assert entity.id == sample_vehicle.id
        assert entity.brand == sample_vehicle.brand
        assert entity.model == sample_vehicle.model
        assert entity.build_year == sample_vehicle.build_year
        assert entity.mileage == sample_vehicle.mileage
        assert entity.fuel_type == sample_vehicle.fuel_type
        assert entity.transmission == sample_vehicle.transmission
        assert entity.engine_volume == sample_vehicle.engine_volume
        assert entity.engine_power == sample_vehicle.engine_power

    def test_search(self, repo):
        now = datetime.now(UTC)
        v1 = Vehicle(
            id="V1",
            url="U1",
            title="Toyota Corolla",
            brand="Toyota",
            model="Corolla",
            price="25000 KM",
            last_visited_at=now,
        )
        v2 = Vehicle(
            id="V2",
            url="U2",
            title="Honda Civic",
            brand="Honda",
            model="Civic",
            price="22000 KM",
            last_visited_at=now - timedelta(days=1),
        )

        repo.add(v1)
        repo.add(v2)

        # search by brand
        results, count = repo.search(brand="Honda")
        assert count == 1
        assert results[0].id == "V2"

        # search by title
        results, count = repo.search(title="Toyota")
        assert count == 1
        assert results[0].id == "V1"

        # search by listing_id
        results, count = repo.search(listing_id="V1")
        assert count == 1

        # search by price range
        results, count = repo.search(min_price=20000, max_price=23000)
        assert count == 1
        assert results[0].id == "V2"

        # search by dates
        results, count = repo.search(min_date=now - timedelta(hours=1))
        assert count == 1
        assert results[0].id == "V1"

        results, count = repo.search(max_date=now - timedelta(hours=1))
        assert count == 1
        assert results[0].id == "V2"

        # search with pagination
        results, count = repo.search(limit=1, offset=0)
        assert len(results) == 1
        assert count == 2

    def test_get_unique_brands(self, repo):
        now = datetime.now(UTC)
        repo.add(
            Vehicle(
                id="v1",
                url="u1",
                title="t1",
                brand="Toyota",
                model="m1",
                price="p1",
                last_visited_at=now,
            )
        )
        repo.add(
            Vehicle(
                id="v2",
                url="u2",
                title="t2",
                brand="Honda",
                model="m2",
                price="p2",
                last_visited_at=now,
            )
        )
        repo.add(
            Vehicle(
                id="v3",
                url="u3",
                title="t3",
                brand="Toyota",
                model="m3",
                price="p3",
                last_visited_at=now,
            )
        )

        brands = repo.get_unique_brands()
        assert "Toyota" in brands
        assert "Honda" in brands
        assert len(brands) == 2
        assert "Volvo" not in brands

    def test_get_new_vehicles_per_run(self, repo, in_memory_db):
        listing_repo = SqlAlchemyListingRepository(in_memory_db)

        now = datetime.now(UTC)
        # create listings associated with runs
        listing_repo.add(
            Listing(id="v1", url="u1", title="t1", price="p1", visited_at=now, run_id="run-1")
        )
        listing_repo.add(
            Listing(
                id="v2",
                url="u2",
                title="t2",
                price="p2",
                visited_at=now + timedelta(seconds=1),
                run_id="run-2",
            )
        )

        # create vehicles for those listings
        repo.add(
            Vehicle(
                id="v1",
                url="u1",
                title="t1",
                brand="B1",
                model="M1",
                price="p1",
                last_visited_at=now,
            )
        )
        repo.add(
            Vehicle(
                id="v2",
                url="u2",
                title="t2",
                brand="B2",
                model="M2",
                price="p2",
                last_visited_at=now,
            )
        )

        metrics = repo.get_new_vehicles_per_run()
        assert len(metrics) == 2

        assert metrics[0]["run_id"] == "run-2"
        assert metrics[0]["new_vehicle_count"] == 1
        assert metrics[1]["run_id"] == "run-1"
        assert metrics[1]["new_vehicle_count"] == 1
