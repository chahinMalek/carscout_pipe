import logging
from datetime import datetime
import copy
from typing import Optional
from pydantic import BaseModel
from carscout_pipe.data_models.vehicles.field_mappings import *


logger = logging.getLogger(__name__)


class Vehicle(BaseModel):
    """Vehicle data model with validation and transformation logic"""

    article_id: int
    title: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    state: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    build_year: Optional[int] = None
    mileage: Optional[int] = None
    engine_volume: Optional[float] = None
    engine_power: Optional[float] = None
    num_doors: Optional[str] = None
    transmission: Optional[str] = None
    image_url: Optional[str] = None
    horsepower: Optional[float] = None
    weight_kg: Optional[float] = None
    vehicle_type: Optional[str] = None
    climate: Optional[str] = None
    audio: Optional[str] = None
    parking_sensors: Optional[str] = None
    parking_camera: Optional[str] = None
    drivetrain: Optional[str] = None
    year_first_registered: Optional[str] = None
    registered_until: Optional[str] = None
    color: Optional[str] = None
    gears: Optional[str] = None
    tyres: Optional[str] = None
    emission: Optional[str] = None
    interior: Optional[str] = None
    curtains: Optional[str] = None
    lights: Optional[str] = None
    number_of_seats: Optional[str] = None
    rim_size: Optional[str] = None
    warranty: Optional[str] = None
    security: Optional[str] = None
    previous_owners: Optional[str] = None
    published_at: Optional[str] = None
    registered: Optional[bool] = None
    metallic: Optional[bool] = None
    alloy_wheels: Optional[bool] = None
    digital_air_conditioning: Optional[bool] = None
    steering_wheel_controls: Optional[bool] = None
    navigation: Optional[bool] = None
    touch_screen: Optional[bool] = None
    heads_up_display: Optional[bool] = None
    usb_port: Optional[bool] = None
    cruise_control: Optional[bool] = None
    bluetooth: Optional[bool] = None
    car_play: Optional[bool] = None
    rain_sensor: Optional[bool] = None
    park_assist: Optional[bool] = None
    automatic_light_sensor: Optional[bool] = None
    blind_spot_sensor: Optional[bool] = None
    start_stop_system: Optional[bool] = None
    hill_assist: Optional[bool] = None
    seat_memory: Optional[bool] = None
    seat_massage: Optional[bool] = None
    seat_heating: Optional[bool] = None
    seat_cooling: Optional[bool] = None
    electric_windows: Optional[bool] = None
    electric_seat_adjustment: Optional[bool] = None
    armrest: Optional[bool] = None
    panoramic_roof: Optional[bool] = None
    sunroof: Optional[bool] = None
    fog_lights: Optional[bool] = None
    electric_mirrors: Optional[bool] = None
    alarm: Optional[bool] = None
    central_lock: Optional[bool] = None
    remote_unlock: Optional[bool] = None
    airbag: Optional[bool] = None
    abs: Optional[bool] = None
    electronic_stability: Optional[bool] = None
    dpf_fap_filter: Optional[bool] = None
    power_steering: Optional[bool] = None
    turbo: Optional[bool] = None
    isofix: Optional[bool] = None
    tow_hook: Optional[bool] = None
    customs_cleared: Optional[bool] = None
    foreign_license_plates: Optional[bool] = None
    on_lease: Optional[bool] = None
    service_history: Optional[bool] = None
    damaged: Optional[bool] = None
    disabled_accessible: Optional[bool] = None
    oldtimer: Optional[bool] = None

    @classmethod
    def from_raw_dict(cls, raw_dict: dict) -> "Vehicle":
        parsed_dict = copy.deepcopy(raw_dict)

        # transform price
        raw_price = raw_dict.get("price")
        if not raw_price or raw_price.lower().strip() == "na upit":
            raw_price = None
        else:
            try:
                raw_price = float(raw_price.split(" ")[0].split(",")[0].replace(".", "").replace("KM", ""))
            except Exception as err:
                logger.error(f"Error transforming price: {err}")
                raw_price = None
        parsed_dict["price"] = raw_price

        # transform mileage
        raw_mileage = raw_dict.get("mileage")
        if raw_mileage:
            try:
                raw_mileage = int(raw_mileage.split(" ")[0].replace(".", "").replace("km", ""))
            except Exception as err:
                logger.error(f"Error transforming mileage: {err}")
                raw_mileage = None
        parsed_dict["mileage"] = raw_mileage

        # transform build year
        raw_build_year = raw_dict.get("build_year")
        if raw_build_year:
            try:
                raw_build_year = int(raw_build_year)
            except Exception as err:
                logger.error(f"Error transforming build year: {err}")
                raw_build_year = None
        parsed_dict["build_year"] = raw_build_year

        # transform published_at
        raw_published_at = raw_dict.get("published_at")
        if raw_published_at:
            try:
                raw_published_at = datetime.strptime(raw_published_at, "%d.%m.%Y").strftime("%Y-%m-%d")
            except Exception as err:
                logger.error(f"Error transforming published at: {err}")
                raw_published_at = None
        parsed_dict["published_at"] = raw_published_at

        # transform article_id
        raw_article_id = raw_dict.get("article_id")
        if raw_article_id:
            try:
                raw_article_id = str(raw_article_id).replace("\n", " ").split(": ")[-1].strip()
                raw_article_id = int(raw_article_id)
            except Exception as err:
                logger.error(f"Error transforming article id: {err}")
                raw_article_id = None
        parsed_dict["article_id"] = raw_article_id

        # apply mappings
        mappings = {
            "fuel_type": FUEL_TYPE_MAPPING,
            "transmission": TRANSMISSION_MAPPING,
            "state": STATE_MAPPING,
            "drivetrain": DRIVETRAIN_MAPPING,
            "climate": CLIMATE_MAPPING,
            "audio": AUDIO_MAPPING,
            "parking_sensors": PARKING_SENSORS_MAPPING,
            "parking_camera": PARKING_CAMERA_MAPPING,
            "interior": INTERIOR_MAPPING,
            "curtains": CURTAIN_MAPPING,
            "lights": LIGHTS_MAPPING,
            "number_of_seats": SEATS_MAPPING,
            "security": SECURITY_MAPPING,
            "tyres": TYRES_MAPPING,
            "previous_owners": PREVIOUS_OWNERS_MAPPING,
            "vehicle_type": TYPE_MAPPING,
            "year_first_registered": FIRST_REGISTERED_MAPPING,
            "color": COLOR_MAPPING,
            "rim_size": RIM_SIZE_MAPPING,
            "warranty": WARRANTY_MAPPING,
        }

        for key, mapping in mappings.items():
            raw_value = raw_dict.get(key)
            if raw_value:
                raw_value = str(raw_value).strip()
                raw_value = mapping.get(raw_value, raw_value)
            parsed_dict[key] = raw_value

        return cls(**parsed_dict)


    class Config:
        """Pydantic model configuration"""
        populate_by_name = True 
