import random
import time
from typing import Any, Dict

import requests
from more_itertools import first
from selenium import webdriver

from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.data_models.vehicles import Vehicle


def init_request_session(driver: webdriver.Chrome) -> requests.Session:
    driver.get("https://olx.ba/pretraga?category_id=18")
    cookies = driver.get_cookies()

    s = requests.Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
    s.headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
    s.headers["referer"] = "https://olx.ba/pretraga?category_id=18"
    s.headers["Accept"] = "application/json, text/plain, */*"

    token = None
    for cookie in cookies:
        if cookie["name"] == "XSRF-TOKEN":
            token = cookie["value"]
    if not token:
        raise ValueError("Failed to fetch auth token.")
    s.headers["X-Xsrf-Token"] = token
    return s


def extract_vehicle_details(
    session: requests.Session,
    listing: Listing,
    min_delay: float = 1,
    max_delay: float = 5,
):
    request_delay = random.uniform(min_delay, max_delay)
    time.sleep(request_delay)
    request_url = f"https://olx.ba/api/listings/{listing.listing_id}"
    response = session.get(request_url)
    if not response.ok:
        return None
    vehicle_data = listing.__dict__
    vehicle_data |= parse_vehicle_info(response.json())
    return Vehicle(**vehicle_data)


def parse_vehicle_info(vehicle_data: dict) -> Dict:
    attributes = vehicle_data.get("attributes") or {}
    attributes = {attr["name"]: attr for attr in attributes}
    return {
        "brand": (vehicle_data.get("brand") or {}).get("name"),
        "model": (vehicle_data.get("model") or {}).get("name"),
        "state": vehicle_data.get("state"),
        "location": (first(vehicle_data.get("cities") or [], default=None) or {}).get(
            "name"
        ),
        "image_url": first(vehicle_data.get("images") or [], default=None),
        "fuel_type": get_attribute_value(attributes.get("Gorivo") or {}),
        "build_year": get_attribute_value(attributes.get("Godište") or {}),
        "mileage": get_attribute_value(attributes.get("Kilometraža") or {}),
        "engine_volume": get_attribute_value(attributes.get("Kubikaža") or {}),
        "engine_power": get_attribute_value(attributes.get("Snaga motora (KW)") or {}),
        "num_doors": get_attribute_value(attributes.get("Broj vrata") or {}),
        "transmission": get_attribute_value(attributes.get("Transmisija") or {}),
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
        "touch_screen": get_attribute_value(
            attributes.get("Touch screen (ekran)") or {}
        ),
        "heads_up_display": get_attribute_value(
            attributes.get("Head up display") or {}
        ),
        "usb_port": get_attribute_value(attributes.get("USB port") or {}),
        "cruise_control": get_attribute_value(attributes.get("Tempomat") or {}),
        "bluetooth": get_attribute_value(attributes.get("Bluetooth") or {}),
        "car_play": get_attribute_value(attributes.get("Car play") or {}),
        "rain_sensor": get_attribute_value(attributes.get("Senzor kiše") or {}),
        "park_assist": get_attribute_value(attributes.get("Park assist") or {}),
        "automatic_light_sensor": get_attribute_value(
            attributes.get("Senzor auto. svjetla") or {}
        ),
        "blind_spot_sensor": get_attribute_value(
            attributes.get("Senzor mrtvog ugla") or {}
        ),
        "start_stop_system": get_attribute_value(
            attributes.get("Start-Stop sistem") or {}
        ),
        "hill_assist": get_attribute_value(attributes.get("Hill assist") or {}),
        "seat_memory": get_attribute_value(attributes.get("Memorija sjedišta") or {}),
        "seat_massage": get_attribute_value(attributes.get("Masaža sjedišta") or {}),
        "seat_heating": get_attribute_value(attributes.get("Grijanje sjedišta") or {}),
        "seat_cooling": get_attribute_value(attributes.get("Hlađenje sjedišta") or {}),
        "electric_windows": get_attribute_value(
            attributes.get("El. podizači stakala") or {}
        ),
        "electric_seat_adjustment": get_attribute_value(
            attributes.get("El. pomjeranje sjedišta") or {}
        ),
        "armrest": get_attribute_value(attributes.get("Naslon za ruku") or {}),
        "panoramic_roof": get_attribute_value(attributes.get("Panorama krov") or {}),
        "sunroof": get_attribute_value(attributes.get("Šiber") or {}),
        "fog_lights": get_attribute_value(attributes.get("Maglenke") or {}),
        "electric_mirrors": get_attribute_value(
            attributes.get("Električni retrovizori") or {}
        ),
        "alarm": get_attribute_value(attributes.get("Alarm") or {}),
        "central_lock": get_attribute_value(attributes.get("Centralna brava") or {}),
        "remote_unlock": get_attribute_value(
            attributes.get("Daljinsko otključavanje") or {}
        ),
        "airbag": get_attribute_value(attributes.get("Airbag") or {}),
        "abs": get_attribute_value(attributes.get("ABS") or {}),
        "electronic_stability": get_attribute_value(attributes.get("ESP") or {}),
        "dpf_fap_filter": get_attribute_value(attributes.get("DPF/FAP filter") or {}),
        "power_steering": get_attribute_value(attributes.get("Servo volan") or {}),
        "turbo": get_attribute_value(attributes.get("Turbo") or {}),
        "isofix": get_attribute_value(attributes.get("ISOFIX") or {}),
        "tow_hook": get_attribute_value(attributes.get("Auto kuka") or {}),
        "customs_cleared": get_attribute_value(attributes.get("Ocarinjen") or {}),
        "foreign_license_plates": get_attribute_value(
            attributes.get("Strane tablice") or {}
        ),
        "on_lease": get_attribute_value(attributes.get("Na lizingu") or {}),
        "service_history": get_attribute_value(attributes.get("Servisna knjiga") or {}),
        "damaged": get_attribute_value(attributes.get("Udaren") or {}),
        "disabled_accessible": get_attribute_value(
            attributes.get("Prilagođen invalidima") or {}
        ),
        "oldtimer": get_attribute_value(attributes.get("Oldtimer") or {}),
    }


def get_attribute_value(attribute_data: dict) -> Any:
    if not attribute_data:
        return None
    value = attribute_data.get("value")
    dtype = attribute_data.get("type")
    if not dtype or not value:
        return value
    if dtype == "number":
        return str(value)
    elif dtype == "string":
        if value in ("true", "false"):
            return {"true": True, "false": False}.get(value)
    return value
