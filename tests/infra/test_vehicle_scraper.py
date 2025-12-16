from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from core.entities.listing import Listing
from core.entities.vehicle import Vehicle
from infra.factory.clients.http import HttpClientFactory
from infra.interfaces.http import HttpClient
from infra.scraping.vehicle_scraper import VehicleScraper


@pytest.mark.unit
class TestVehicleScraper:
    @pytest.fixture
    def mock_http_client_factory(self):
        return Mock(spec=HttpClientFactory)

    @pytest.fixture
    def mock_http_client(self):
        return Mock(spec=HttpClient)

    @pytest.fixture
    def scraper(self, mock_logger_factory, mock_http_client_factory):
        return VehicleScraper(
            logger_factory=mock_logger_factory,
            http_client_factory=mock_http_client_factory,
            min_req_delay=1.0,
            max_req_delay=2.0,
            timeout=5.0,
            reinit_session_every=500,
        )

    @pytest.fixture
    def sample_listing(self):
        return Listing(
            id="11111",
            url="https://olx.ba/artikal/11111",
            title="BMW M3",
            price="40.000 KM",
            visited_at=datetime(2025, 12, 16, 10, 0, 0),
            run_id="run_001",
        )

    @pytest.fixture
    def sample_api_response(self):
        return {
            "id": 11111,
            "title": "BMW M3",
            "price": "40.000 KM",
            "state": "active",
            "cities": [{"name": "Sarajevo"}],
            "brand": {"name": "BMW"},
            "model": {"name": "M3"},
            "images": ["https://example.com/image1.jpg"],
            "attributes": [
                {"name": "Gorivo", "value": "Dizel", "type": "string"},
                {"name": "Godište", "value": "2015", "type": "number"},
                {"name": "Kilometraža", "value": "150.000 km", "type": "string"},
                {"name": "Kubikaža", "value": "2.0", "type": "string"},
                {"name": "Snaga motora (KW)", "value": "140", "type": "number"},
                {"name": "Broj vrata", "value": "4", "type": "string"},
                {"name": "Transmisija", "value": "Automatik", "type": "string"},
                {"name": "Registrovan", "value": "true", "type": "string"},
                {"name": "Metalik", "value": "true", "type": "string"},
                {"name": "Alu felge", "value": "true", "type": "string"},
            ],
        }

    def test_parse_vehicle_info(self, scraper, sample_api_response):
        result = scraper._parse_vehicle_info(sample_api_response)

        assert result["location"] == "Sarajevo"
        assert result["state"] == "active"
        assert result["brand"] == "BMW"
        assert result["model"] == "M3"
        assert result["image_url"] == "https://example.com/image1.jpg"

        assert result["fuel_type"] == "Dizel"
        assert result["build_year"] == "2015"
        assert result["mileage"] == "150.000 km"
        assert result["engine_volume"] == "2.0"
        assert result["engine_power"] == "140"
        assert result["num_doors"] == "4"
        assert result["transmission"] == "Automatik"

        assert result["registered"] is True
        assert result["metallic"] is True
        assert result["alloy_wheels"] is True

    def test_get_vehicle_info_success(
        self, scraper, mock_http_client, sample_listing, sample_api_response
    ):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = sample_api_response
        mock_http_client.get.return_value = mock_response

        with patch("time.sleep") as mock_sleep:
            vehicle = scraper._get_vehicle_info(sample_listing, mock_http_client)

            mock_sleep.assert_called_once()
            delay_arg = mock_sleep.call_args[0][0]
            assert scraper._min_req_delay <= delay_arg <= scraper._max_req_delay

        # check if api request was made
        expected_url = "https://olx.ba/api/listings/11111"
        mock_http_client.get.assert_called_once_with(expected_url, timeout=5.0)

        # check result
        assert isinstance(vehicle, Vehicle)
        assert vehicle.id == sample_listing.id
        assert vehicle.url == sample_listing.url
        assert vehicle.title == sample_listing.title
        assert vehicle.price == sample_listing.price
        assert vehicle.last_visited_at == sample_listing.visited_at

    def test_get_vehicle_info_error(self, scraper, mock_http_client, sample_listing):
        mock_response = Mock()
        mock_response.ok = False
        mock_http_client.get.return_value = mock_response

        with patch("time.sleep"):
            vehicle = scraper._get_vehicle_info(sample_listing, mock_http_client)

        assert vehicle is None

    def test_run_success(
        self, scraper, mock_http_client_factory, mock_http_client, sample_api_response
    ):
        mock_http_client_factory.create.return_value = mock_http_client
        listings = [
            Listing(
                id="11111",
                url="https://olx.ba/api/listings/11111",
                title="BMW M3",
                price="40.000 KM",
            ),
            Listing(
                id="22222",
                url="https://olx.ba/api/listings/22222",
                title="Audi A4",
                price="30.000 KM",
            ),
            Listing(
                id="33333",
                url="https://olx.ba/api/listings/33333",
                title="Mercedes C250",
                price="25.000 KM",
            ),
        ]

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = sample_api_response
        mock_http_client.get.return_value = mock_response

        with patch("time.sleep"):
            vehicles = list(scraper.run(listings))

        # ensure http client was created
        mock_http_client_factory.create.assert_called_once()

        # check result
        assert len(vehicles) == 3
        assert all(isinstance(v, Vehicle) for v in vehicles)
        assert vehicles[0].id == "11111"
        assert vehicles[1].id == "22222"
        assert vehicles[2].id == "33333"

    def test_run_fail(
        self, scraper, mock_http_client_factory, mock_http_client, sample_api_response
    ):
        mock_http_client_factory.create.return_value = mock_http_client

        listings = [
            Listing(
                id="11111",
                url="https://olx.ba/api/listings/11111",
                title="BMW M3",
                price="40.000 KM",
            ),
            Listing(
                id="22222",
                url="https://olx.ba/api/listings/22222",
                title="Audi A4",
                price="30.000 KM",
            ),
            Listing(
                id="33333",
                url="https://olx.ba/api/listings/33333",
                title="Mercedes C250",
                price="25.000 KM",
            ),
        ]

        # first response is ok
        mock_response_ok = Mock()
        mock_response_ok.ok = True
        mock_response_ok.json.return_value = sample_api_response

        # ... second one has an error
        mock_response_fail = Mock()
        mock_response_fail.ok = False

        # ... third one is a success as well

        mock_http_client.get.side_effect = [mock_response_ok, mock_response_fail, mock_response_ok]

        with patch("time.sleep"):
            vehicles = list(scraper.run(listings))

        # only the first and last one should be present in the result
        assert len(vehicles) == 2
        assert vehicles[0].id == "11111"
        assert vehicles[1].id == "33333"

    def test_run_session_reinit(
        self, scraper, mock_http_client_factory, mock_http_client, sample_api_response
    ):
        scraper._reinit_session_every = 2
        mock_http_client_factory.create.return_value = mock_http_client

        listings = [
            Listing(
                id="11111",
                url="https://olx.ba/api/listings/11111",
                title="BMW M3",
                price="40.000 KM",
            ),
            Listing(
                id="22222",
                url="https://olx.ba/api/listings/22222",
                title="Audi A4",
                price="30.000 KM",
            ),
            Listing(
                id="33333",
                url="https://olx.ba/api/listings/33333",
                title="Mercedes C250",
                price="25.000 KM",
            ),
            Listing(
                id="44444",
                url="https://olx.ba/api/listings/44444",
                title="BMW M3",
                price="40.000 KM",
            ),
            Listing(
                id="55555",
                url="https://olx.ba/api/listings/55555",
                title="Audi A4",
                price="30.000 KM",
            ),
            Listing(
                id="66666",
                url="https://olx.ba/api/listings/66666",
                title="Mercedes C250",
                price="25.000 KM",
            ),
        ]

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = sample_api_response
        mock_http_client.get.return_value = mock_response

        with patch("time.sleep"):
            list(scraper.run(listings))

        # once before the loop
        # once after id=22222
        # once after id=44444
        # once after id=66666
        assert mock_http_client_factory.create.call_count == 4
