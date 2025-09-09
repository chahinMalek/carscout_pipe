from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from .base import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Linking fields (for connecting to listings)
    listing_id = Column(String, nullable=False, unique=True, index=True)
    url = Column(Text, nullable=False)

    # Listing fields
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)

    # Basic vehicle information
    location = Column(String, nullable=True)
    state = Column(String, nullable=True)
    article_id = Column(String, nullable=True)
    brand = Column(String, nullable=True, index=True)
    model = Column(String, nullable=True, index=True)
    fuel_type = Column(String, nullable=True)
    build_year = Column(String, nullable=True, index=True)
    mileage = Column(String, nullable=True)
    engine_volume = Column(String, nullable=True)
    engine_power = Column(String, nullable=True)
    num_doors = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    image_url = Column(Text, nullable=True)
    
    # Extended vehicle details
    horsepower = Column(String, nullable=True)
    weight_kg = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    climate = Column(String, nullable=True)
    audio = Column(String, nullable=True)
    parking_sensors = Column(String, nullable=True)
    parking_camera = Column(String, nullable=True)
    drivetrain = Column(String, nullable=True)
    year_first_registered = Column(String, nullable=True)
    registered_until = Column(String, nullable=True)
    color = Column(String, nullable=True)
    gears = Column(String, nullable=True)
    tyres = Column(String, nullable=True)
    emission = Column(String, nullable=True)
    interior = Column(String, nullable=True)
    curtains = Column(String, nullable=True)
    lights = Column(String, nullable=True)
    number_of_seats = Column(String, nullable=True)
    rim_size = Column(String, nullable=True)
    warranty = Column(String, nullable=True)
    security = Column(String, nullable=True)
    previous_owners = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    
    # Boolean features
    # sold = Column(Boolean, nullable=True)
    registered = Column(Boolean, nullable=True)
    metallic = Column(Boolean, nullable=True)
    alloy_wheels = Column(Boolean, nullable=True)
    digital_air_conditioning = Column(Boolean, nullable=True)
    steering_wheel_controls = Column(Boolean, nullable=True)
    navigation = Column(Boolean, nullable=True)
    touch_screen = Column(Boolean, nullable=True)
    heads_up_display = Column(Boolean, nullable=True)
    usb_port = Column(Boolean, nullable=True)
    cruise_control = Column(Boolean, nullable=True)
    bluetooth = Column(Boolean, nullable=True)
    car_play = Column(Boolean, nullable=True)
    rain_sensor = Column(Boolean, nullable=True)
    park_assist = Column(Boolean, nullable=True)
    automatic_light_sensor = Column(Boolean, nullable=True)
    blind_spot_sensor = Column(Boolean, nullable=True)
    start_stop_system = Column(Boolean, nullable=True)
    hill_assist = Column(Boolean, nullable=True)
    seat_memory = Column(Boolean, nullable=True)
    seat_massage = Column(Boolean, nullable=True)
    seat_heating = Column(Boolean, nullable=True)
    seat_cooling = Column(Boolean, nullable=True)
    electric_windows = Column(Boolean, nullable=True)
    electric_seat_adjustment = Column(Boolean, nullable=True)
    armrest = Column(Boolean, nullable=True)
    panoramic_roof = Column(Boolean, nullable=True)
    sunroof = Column(Boolean, nullable=True)
    fog_lights = Column(Boolean, nullable=True)
    electric_mirrors = Column(Boolean, nullable=True)
    alarm = Column(Boolean, nullable=True)
    central_lock = Column(Boolean, nullable=True)
    remote_unlock = Column(Boolean, nullable=True)
    airbag = Column(Boolean, nullable=True)
    abs = Column(Boolean, nullable=True)
    electronic_stability = Column(Boolean, nullable=True)
    dpf_fap_filter = Column(Boolean, nullable=True)
    power_steering = Column(Boolean, nullable=True)
    turbo = Column(Boolean, nullable=True)
    isofix = Column(Boolean, nullable=True)
    tow_hook = Column(Boolean, nullable=True)
    customs_cleared = Column(Boolean, nullable=True)
    foreign_license_plates = Column(Boolean, nullable=True)
    on_lease = Column(Boolean, nullable=True)
    service_history = Column(Boolean, nullable=True)
    damaged = Column(Boolean, nullable=True)
    disabled_accessible = Column(Boolean, nullable=True)
    oldtimer = Column(Boolean, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime, default=datetime.now(), nullable=False)
    run_id = Column(String, nullable=False)
