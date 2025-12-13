from datetime import UTC, datetime

import pytest

from core.entities.vehicle import Vehicle
from infra.db.models.vehicle import VehicleModel
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
