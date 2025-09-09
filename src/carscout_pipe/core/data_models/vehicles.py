from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Vehicle:
    """Vehicle data model containing all scraped vehicle attributes."""
    
    # Listing fields
    listing_id: str
    url: str
    title: str
    price: str

    # Basic vehicle information
    location: Optional[str] = None
    state: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    build_year: Optional[str] = None
    mileage: Optional[str] = None
    engine_volume: Optional[str] = None
    engine_power: Optional[str] = None
    num_doors: Optional[str] = None
    transmission: Optional[str] = None
    image_url: Optional[str] = None
    
    # Extended vehicle details
    horsepower: Optional[str] = None
    weight_kg: Optional[str] = None
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
    
    # Boolean features
    # sold: Optional[bool] = None
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
