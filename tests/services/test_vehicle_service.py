from unittest.mock import Mock

import pytest

from core.entities.vehicle import Vehicle
from core.services.vehicle_service import VehicleService


@pytest.fixture
def mock_repo():
    """Create a mock VehicleRepository for testing."""
    return Mock()


@pytest.fixture
def service(mock_repo):
    """Create a VehicleService with mocked repository."""
    return VehicleService(repo=mock_repo)


class TestCreateListing:
    """Tests for the create_listing static method."""

    def test_create_listing_from_dict_basic_fields(self):
        """Test creating a vehicle from a dictionary with basic fields."""
        data = {
            "id": "vehicle123",
            "url": "https://example.com/vehicle123",
            "title": "BMW 3 Series",
            "price": "35,000 KM",
        }
        vehicle = VehicleService.create_listing(data)

        assert isinstance(vehicle, Vehicle)
        assert vehicle.id == "vehicle123"
        assert vehicle.url == "https://example.com/vehicle123"
        assert vehicle.title == "BMW 3 Series"
        assert vehicle.price == "35,000 KM"

    def test_create_listing_with_extended_fields(self):
        """Test creating a vehicle with extended vehicle details."""
        data = {
            "id": "vehicle456",
            "url": "https://example.com/vehicle456",
            "title": "Audi A4",
            "price": "40,000 KM",
            "brand": "Audi",
            "model": "A4",
            "fuel_type": "Diesel",
            "build_year": 2020,
            "mileage": "50000 km",
            "transmission": "Automatic",
            "horsepower": 190,
            "color": "Black",
        }
        vehicle = VehicleService.create_listing(data)

        assert vehicle.id == "vehicle456"
        assert vehicle.brand == "Audi"
        assert vehicle.model == "A4"
        assert vehicle.fuel_type == "Diesel"
        assert vehicle.build_year == 2020
        assert vehicle.mileage == "50000 km"
        assert vehicle.transmission == "Automatic"
        assert vehicle.horsepower == 190
        assert vehicle.color == "Black"

    def test_create_listing_ignores_extra_fields(self):
        """Test that extra fields not in Vehicle dataclass are ignored."""
        data = {
            "id": "vehicle789",
            "url": "https://example.com/vehicle789",
            "title": "Mercedes C-Class",
            "price": "45,000 KM",
            "extra_field": "should be ignored",
            "another_field": 123,
        }
        vehicle = VehicleService.create_listing(data)

        assert vehicle.id == "vehicle789"
        assert not hasattr(vehicle, "extra_field")
        assert not hasattr(vehicle, "another_field")


class TestInsertVehicle:
    """Tests for the insert_vehicle method."""

    def test_insert_vehicle_success(self, service, mock_repo):
        """Test successfully inserting a vehicle."""
        vehicle = Vehicle(
            id="vehicle111",
            url="https://example.com/vehicle111",
            title="Tesla Model 3",
            price="50,000 KM",
            brand="Tesla",
            model="Model 3",
        )
        mock_repo.add.return_value = vehicle

        result = service.insert_vehicle(vehicle)

        mock_repo.add.assert_called_once_with(vehicle)
        assert result == vehicle

    def test_insert_vehicle_calls_repo(self, service, mock_repo):
        """Test that insert_vehicle delegates to repository."""
        vehicle = Vehicle(
            id="vehicle222",
            url="https://example.com/vehicle222",
            title="Porsche 911",
            price="120,000 KM",
        )

        service.insert_vehicle(vehicle)

        mock_repo.add.assert_called_once_with(vehicle)


class TestVehicleExists:
    """Tests for the vehicle_exists method."""

    def test_vehicle_exists_returns_true_when_found(self, service, mock_repo):
        """Test vehicle_exists returns True when vehicle is found."""
        vehicle = Vehicle(
            id="vehicle333",
            url="https://example.com/vehicle333",
            title="Ford Mustang",
            price="60,000 KM",
        )
        mock_repo.get.return_value = vehicle

        result = service.vehicle_exists("vehicle333")

        mock_repo.get.assert_called_once_with("vehicle333")
        assert result is True

    def test_vehicle_exists_returns_false_when_not_found(self, service, mock_repo):
        """Test vehicle_exists returns False when vehicle is not found."""
        mock_repo.get.return_value = None

        result = service.vehicle_exists("nonexistent")

        mock_repo.get.assert_called_once_with("nonexistent")
        assert result is False


class TestGetVehicle:
    """Tests for the get_vehicle method."""

    def test_get_vehicle_existing(self, service, mock_repo):
        """Test getting an existing vehicle."""
        vehicle = Vehicle(
            id="vehicle444",
            url="https://example.com/vehicle444",
            title="Volkswagen Golf",
            price="25,000 KM",
            brand="Volkswagen",
            model="Golf",
        )
        mock_repo.get.return_value = vehicle

        result = service.get_vehicle("vehicle444")

        mock_repo.get.assert_called_once_with("vehicle444")
        assert result == vehicle
        assert result.brand == "Volkswagen"
        assert result.model == "Golf"

    def test_get_vehicle_nonexistent(self, service, mock_repo):
        """Test getting a vehicle that doesn't exist."""
        mock_repo.get.return_value = None

        result = service.get_vehicle("nonexistent")

        mock_repo.get.assert_called_once_with("nonexistent")
        assert result is None


class TestVehicleServiceIntegration:
    """Integration-style tests for VehicleService."""

    def test_workflow_create_and_insert_vehicle(self, service, mock_repo):
        """Test typical workflow: create vehicle from dict and insert."""
        data = {
            "id": "vehicle555",
            "url": "https://example.com/vehicle555",
            "title": "Honda Civic",
            "price": "28,000 KM",
            "brand": "Honda",
            "model": "Civic",
            "fuel_type": "Hybrid",
        }

        # Create vehicle
        vehicle = VehicleService.create_listing(data)
        assert vehicle.brand == "Honda"

        # Mock the insert
        mock_repo.add.return_value = vehicle

        # Insert vehicle
        result = service.insert_vehicle(vehicle)

        mock_repo.add.assert_called_once_with(vehicle)
        assert result.id == "vehicle555"

    def test_workflow_check_exists_then_get(self, service, mock_repo):
        """Test workflow: check if vehicle exists, then get it."""
        vehicle = Vehicle(
            id="vehicle666",
            url="https://example.com/vehicle666",
            title="Mazda MX-5",
            price="32,000 KM",
        )

        # Mock existence check
        mock_repo.get.return_value = vehicle

        # Check exists
        exists = service.vehicle_exists("vehicle666")
        assert exists is True

        # Get vehicle
        result = service.get_vehicle("vehicle666")
        assert result == vehicle
        assert mock_repo.get.call_count == 2
