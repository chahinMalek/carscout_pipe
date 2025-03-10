from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from src.value_mappings import *


class Vehicle(BaseModel):
    """Vehicle data model with validation and transformation logic"""

    title: str
    price: Optional[float] = None
    location: Optional[str] = None
    state: Optional[str] = None
    article_id: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    build_year: Optional[int] = None
    mileage: Optional[int] = None
    engine_volume: Optional[float] = None
    engine_power: Optional[int] = None
    num_doors: Optional[str] = None
    transmission: Optional[str] = None
    image_url: Optional[str] = None
    horsepower: Optional[int] = None
    weight_kg: Optional[int] = None
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

    @field_validator('price', mode='before')
    @classmethod
    def transform_price(cls, v):
        if not v or v.lower().strip() == "na upit":
            return None
        try:
            price_str = v.split(" ")[0].replace(".", "").replace("KM", "")
            return float(price_str.replace(",", "."))
        except (ValueError, AttributeError):
            return None

    @field_validator('mileage', mode='before')
    @classmethod
    def transform_mileage(cls, v):
        if not v:
            return None
        try:
            return int(v.split(" ")[0].replace(".", "").replace("km", ""))
        except (ValueError, AttributeError):
            return None

    @field_validator('build_year', mode='before')
    @classmethod
    def transform_year(cls, v):
        if not v:
            return None
        try:
            return int(v)
        except (ValueError, AttributeError):
            return None

    @field_validator('published_at', mode='before')
    @classmethod
    def transform_date(cls, v):
        if not v:
            return None
        try:
            return datetime.strptime(v, "%d.%m.%Y").strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None

    @field_validator('article_id', mode='before')
    @classmethod
    def transform_article_id(cls, v):
        if not v:
            return None
        return v.replace("\n", " ").split(": ")[-1].strip()

    @field_validator('fuel_type', mode='before')
    @classmethod
    def map_fuel_type(cls, v):
        if not v:
            return None
        return FUEL_TYPE_MAPPING.get(v.strip(), v)

    @field_validator('transmission', mode='before')
    @classmethod
    def map_transmission(cls, v):
        if not v:
            return None
        return TRANSMISSION_MAPPING.get(v.strip(), v)

    @field_validator('state', mode='before')
    @classmethod
    def map_state(cls, v):
        if not v:
            return None
        return STATE_MAPPING.get(v.strip(), v)

    @field_validator('drivetrain', mode='before')
    @classmethod
    def map_drivetrain(cls, v):
        if not v:
            return None
        return DRIVETRAIN_MAPPING.get(v.strip(), v)

    @field_validator('climate', mode='before')
    @classmethod
    def map_climate(cls, v):
        if not v:
            return None
        return CLIMATE_MAPPING.get(v.strip(), v)

    @field_validator('audio', mode='before')
    @classmethod
    def map_audio(cls, v):
        if not v:
            return None
        return AUDIO_MAPPING.get(v.strip(), v)

    @field_validator('parking_sensors', mode='before')
    @classmethod
    def map_parking_sensors(cls, v):
        if not v:
            return None
        return PARKING_SENSORS_MAPPING.get(v.strip(), v)

    @field_validator('parking_camera', mode='before')
    @classmethod
    def map_parking_camera(cls, v):
        if not v:
            return None
        return PARKING_CAMERA_MAPPING.get(v.strip(), v)

    @field_validator('interior', mode='before')
    @classmethod
    def map_interior(cls, v):
        if not v:
            return None
        return INTERIOR_MAPPING.get(v.strip(), v)

    @field_validator('curtains', mode='before')
    @classmethod
    def map_curtains(cls, v):
        if not v:
            return None
        return CURTAIN_MAPPING.get(v.strip(), v)

    @field_validator('lights', mode='before')
    @classmethod
    def map_lights(cls, v):
        if not v:
            return None
        return LIGHTS_MAPPING.get(v.strip(), v)

    @field_validator('number_of_seats', mode='before')
    @classmethod
    def map_number_of_seats(cls, v):
        if not v:
            return None
        return SEATS_MAPPING.get(v.strip(), v)

    @field_validator('security', mode='before')
    @classmethod
    def map_security(cls, v):
        if not v:
            return None
        return SECURITY_MAPPING.get(v.strip(), v)

    @field_validator('tyres', mode='before')
    @classmethod
    def map_tyres(cls, v):
        if not v:
            return None
        return TYRES_MAPPING.get(v.strip(), v)

    @field_validator('previous_owners', mode='before')
    @classmethod
    def map_previous_owners(cls, v):
        if not v:
            return None
        return PREVIOUS_OWNERS_MAPPING.get(v.strip(), v)

    @field_validator('vehicle_type', mode='before')
    @classmethod
    def map_vehicle_type(cls, v):
        if not v:
            return None
        return TYPE_MAPPING.get(v.strip(), v)

    @field_validator('year_first_registered', mode='before')
    @classmethod
    def map_year_first_registered(cls, v):
        if not v:
            return None
        return FIRST_REGISTERED_MAPPING.get(v.strip(), v)

    @field_validator('color', mode='before')
    @classmethod
    def map_color(cls, v):
        if not v:
            return None
        return COLOR_MAPPING.get(v.strip(), v)

    @field_validator('rim_size', mode='before')
    @classmethod
    def map_rim_size(cls, v):
        if not v:
            return None
        return RIM_SIZE_MAPPING.get(v.strip(), v)

    @field_validator('warranty', mode='before')
    @classmethod
    def map_warranty(cls, v):
        if not v:
            return None
        return WARRANTY_MAPPING.get(v.strip(), v)


    class Config:
        """Pydantic model configuration"""
        populate_by_name = True 
