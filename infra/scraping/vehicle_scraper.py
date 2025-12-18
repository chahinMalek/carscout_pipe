import random
import time
from collections.abc import Generator
from dataclasses import asdict

from backoff import expo, on_exception
from more_itertools import first

from core.entities.listing import Listing
from core.entities.vehicle import Vehicle
from infra.factory.clients.http import HttpClientFactory
from infra.factory.logger import LoggerFactory
from infra.interfaces.http import HttpClient
from infra.scraping.base import Scraper
from infra.utils.parsing import get_attribute_value


class VehicleScraper(Scraper):
    def __init__(
        self,
        logger_factory: LoggerFactory,
        http_client_factory: HttpClientFactory,
        min_req_delay: float = 1.0,
        max_req_delay: float = 3.0,
        timeout: float = 10.0,
        reinit_session_every: int = 500,
    ):
        super().__init__(logger_factory)
        self._http_client_factory = http_client_factory
        self._min_req_delay = min_req_delay
        self._max_req_delay = max_req_delay
        self._timeout = timeout
        self._reinit_session_every = reinit_session_every

    @property
    def scraper_id(self) -> str:
        return "vehicle_scraper"

    def run(self, listings: list[Listing]) -> Generator[Vehicle, None, None]:
        try:
            http_client = self._http_client_factory.create()
            for idx, listing in enumerate(listings, start=1):
                try:
                    if idx % self._reinit_session_every == 0:
                        self._logger.info("Reinit http client session ...")
                        http_client = self._http_client_factory.create()
                    vehicle = self._get_vehicle_info(listing, http_client)
                    if vehicle is None:
                        self._logger.info(
                            f"Failed to extract vehicle details for listing: {listing.id}"
                        )
                except Exception as err:
                    self._logger.error(
                        f"Unexpected error occurred during scraping listing.id={listing.id}: {err}"
                    )
                yield vehicle
        except Exception as err:
            self._logger.error(f"Unexpected error occurred during vehicle info scraping: {err}")

    @on_exception(expo, Exception, max_tries=3, max_time=60)
    def _get_vehicle_info(self, listing: Listing, http_client: HttpClient):
        req_delay = random.uniform(self._min_req_delay, self._max_req_delay)
        self._logger.debug(f"Sleeping before request for {req_delay:.4f} seconds.")
        time.sleep(req_delay)
        request_url = f"https://olx.ba/api/listings/{listing.id}"
        self._logger.debug(f"Retrieving vehicle info from {request_url}")
        response = http_client.get(request_url, timeout=self._timeout)
        if not response.ok:
            return None
        parsed_data = self._parse_vehicle_info(response.json())
        listing_data = asdict(listing)
        listing_data.pop("run_id", None)
        listing_data["last_visited_at"] = listing_data.pop("visited_at", None)
        return Vehicle.from_dict(listing_data | parsed_data)

    def _parse_vehicle_info(self, vehicle_data: dict) -> dict:
        attributes = vehicle_data.get("attributes") or {}
        attributes = {attr["name"]: attr for attr in attributes}
        return {
            "location": (first(vehicle_data.get("cities") or [], default=None) or {}).get("name"),
            "state": vehicle_data.get("state"),
            "brand": (vehicle_data.get("brand") or {}).get("name"),
            "model": (vehicle_data.get("model") or {}).get("name"),
            "fuel_type": get_attribute_value(attributes.get("Gorivo") or {}),
            "build_year": get_attribute_value(attributes.get("Godište") or {}),
            "mileage": get_attribute_value(attributes.get("Kilometraža") or {}),
            "engine_volume": get_attribute_value(attributes.get("Kubikaža") or {}),
            "engine_power": get_attribute_value(attributes.get("Snaga motora (KW)") or {}),
            "num_doors": get_attribute_value(attributes.get("Broj vrata") or {}),
            "transmission": get_attribute_value(attributes.get("Transmisija") or {}),
            "image_url": first(vehicle_data.get("images") or [], default=None),
            "horsepower": get_attribute_value(attributes.get("Konjskih snaga") or {}),
            "weight_kg": get_attribute_value(attributes.get("Masa/Težina (kg)") or {}),
            "vehicle_type": get_attribute_value(attributes.get("Tip") or {}),
            "climate": get_attribute_value(attributes.get("Klimatizacija") or {}),
            "audio": get_attribute_value(attributes.get("Muzika/ozvučenje") or {}),
            "parking_sensors": get_attribute_value(attributes.get("Parking senzori") or {}),
            "parking_camera": get_attribute_value(attributes.get("Parking kamera") or {}),
            "drivetrain": get_attribute_value(attributes.get("Pogon") or {}),
            "year_first_registered": get_attribute_value(
                attributes.get("Godina prve registracije") or {}
            ),
            "registered_until": get_attribute_value(attributes.get("Registrovan do") or {}),
            "color": get_attribute_value(attributes.get("Boja") or {}),
            "gears": get_attribute_value(attributes.get("Broj stepeni prijenosa") or {}),
            "tyres": get_attribute_value(attributes.get("Posjeduje gume") or {}),
            "emission": get_attribute_value(attributes.get("Emisioni standard") or {}),
            "interior": get_attribute_value(attributes.get("Vrsta enterijera") or {}),
            "curtains": get_attribute_value(attributes.get("Rolo zavjese") or {}),
            "lights": get_attribute_value(attributes.get("Svjetla") or {}),
            "number_of_seats": get_attribute_value(attributes.get("Sjedećih mjesta") or {}),
            "rim_size": get_attribute_value(attributes.get("Veličina felgi") or {}),
            "warranty": get_attribute_value(attributes.get("Garancija") or {}),
            "security": get_attribute_value(attributes.get("Zaštita/Blokada") or {}),
            "previous_owners": get_attribute_value(
                attributes.get("Broj prethodnih vlasnika") or {}
            ),
            "published_at": get_attribute_value(attributes.get("Datum objave") or {}),
            "registered": get_attribute_value(attributes.get("Registrovan") or {}),
            "metallic": get_attribute_value(attributes.get("Metalik") or {}),
            "alloy_wheels": get_attribute_value(attributes.get("Alu felge") or {}),
            "digital_air_conditioning": get_attribute_value(
                attributes.get("Digitalna klima") or {}
            ),
            "steering_wheel_controls": get_attribute_value(
                attributes.get("Komande na volanu") or {}
            ),
            "navigation": get_attribute_value(attributes.get("Navigacija") or {}),
            "touch_screen": get_attribute_value(attributes.get("Touch screen (ekran)") or {}),
            "heads_up_display": get_attribute_value(attributes.get("Head up display") or {}),
            "usb_port": get_attribute_value(attributes.get("USB port") or {}),
            "cruise_control": get_attribute_value(attributes.get("Tempomat") or {}),
            "bluetooth": get_attribute_value(attributes.get("Bluetooth") or {}),
            "car_play": get_attribute_value(attributes.get("Car play") or {}),
            "rain_sensor": get_attribute_value(attributes.get("Senzor kiše") or {}),
            "park_assist": get_attribute_value(attributes.get("Park assist") or {}),
            "automatic_light_sensor": get_attribute_value(
                attributes.get("Senzor auto. svjetla") or {}
            ),
            "blind_spot_sensor": get_attribute_value(attributes.get("Senzor mrtvog ugla") or {}),
            "start_stop_system": get_attribute_value(attributes.get("Start-Stop sistem") or {}),
            "hill_assist": get_attribute_value(attributes.get("Hill assist") or {}),
            "seat_memory": get_attribute_value(attributes.get("Memorija sjedišta") or {}),
            "seat_massage": get_attribute_value(attributes.get("Masaža sjedišta") or {}),
            "seat_heating": get_attribute_value(attributes.get("Grijanje sjedišta") or {}),
            "seat_cooling": get_attribute_value(attributes.get("Hlađenje sjedišta") or {}),
            "electric_windows": get_attribute_value(attributes.get("El. podizači stakala") or {}),
            "electric_seat_adjustment": get_attribute_value(
                attributes.get("El. pomjeranje sjedišta") or {}
            ),
            "armrest": get_attribute_value(attributes.get("Naslon za ruku") or {}),
            "panoramic_roof": get_attribute_value(attributes.get("Panorama krov") or {}),
            "sunroof": get_attribute_value(attributes.get("Šiber") or {}),
            "fog_lights": get_attribute_value(attributes.get("Maglenke") or {}),
            "electric_mirrors": get_attribute_value(attributes.get("Električni retrovizori") or {}),
            "alarm": get_attribute_value(attributes.get("Alarm") or {}),
            "central_lock": get_attribute_value(attributes.get("Centralna brava") or {}),
            "remote_unlock": get_attribute_value(attributes.get("Daljinsko otključavanje") or {}),
            "airbag": get_attribute_value(attributes.get("Airbag") or {}),
            "abs": get_attribute_value(attributes.get("ABS") or {}),
            "electronic_stability": get_attribute_value(attributes.get("ESP") or {}),
            "dpf_fap_filter": get_attribute_value(attributes.get("DPF/FAP filter") or {}),
            "power_steering": get_attribute_value(attributes.get("Servo volan") or {}),
            "turbo": get_attribute_value(attributes.get("Turbo") or {}),
            "isofix": get_attribute_value(attributes.get("ISOFIX") or {}),
            "tow_hook": get_attribute_value(attributes.get("Auto kuka") or {}),
            "customs_cleared": get_attribute_value(attributes.get("Ocarinjen") or {}),
            "foreign_license_plates": get_attribute_value(attributes.get("Strane tablice") or {}),
            "on_lease": get_attribute_value(attributes.get("Na lizingu") or {}),
            "service_history": get_attribute_value(attributes.get("Servisna knjiga") or {}),
            "damaged": get_attribute_value(attributes.get("Udaren") or {}),
            "disabled_accessible": get_attribute_value(
                attributes.get("Prilagođen invalidima") or {}
            ),
            "oldtimer": get_attribute_value(attributes.get("Oldtimer") or {}),
        }
