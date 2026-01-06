from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from infra.db.models.base import Base, SQLiteSafeDateTime


class VehicleModel(Base):
    __tablename__ = "vehicles"

    # primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # listing fields
    listing_id = Column(String, unique=True, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)
    last_visited_at = Column(SQLiteSafeDateTime, nullable=True)

    # basic vehicle information
    location = Column(String, nullable=True)
    state = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    fuel_type = Column(String, nullable=True)
    build_year = Column(Integer, nullable=True)
    mileage = Column(String, nullable=True)
    engine_volume = Column(String, nullable=True)
    engine_power = Column(Integer, nullable=True)
    num_doors = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    # extended vehicle details
    horsepower = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    vehicle_type = Column(String, nullable=True)
    climate = Column(String, nullable=True)
    audio = Column(String, nullable=True)
    parking_sensors = Column(String, nullable=True)
    parking_camera = Column(String, nullable=True)
    drivetrain = Column(String, nullable=True)
    year_first_registered = Column(Integer, nullable=True)
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
    published_at = Column(SQLiteSafeDateTime, nullable=True)

    # boolean fields
    registered = Column(String, nullable=True)
    metallic = Column(String, nullable=True)
    alloy_wheels = Column(String, nullable=True)
    digital_air_conditioning = Column(String, nullable=True)
    steering_wheel_controls = Column(String, nullable=True)
    navigation = Column(String, nullable=True)
    touch_screen = Column(String, nullable=True)
    heads_up_display = Column(String, nullable=True)
    usb_port = Column(String, nullable=True)
    cruise_control = Column(String, nullable=True)
    bluetooth = Column(String, nullable=True)
    car_play = Column(String, nullable=True)
    rain_sensor = Column(String, nullable=True)
    park_assist = Column(String, nullable=True)
    automatic_light_sensor = Column(String, nullable=True)
    blind_spot_sensor = Column(String, nullable=True)
    start_stop_system = Column(String, nullable=True)
    hill_assist = Column(String, nullable=True)
    seat_memory = Column(String, nullable=True)
    seat_massage = Column(String, nullable=True)
    seat_heating = Column(String, nullable=True)
    seat_cooling = Column(String, nullable=True)
    electric_windows = Column(String, nullable=True)
    electric_seat_adjustment = Column(String, nullable=True)
    armrest = Column(String, nullable=True)
    panoramic_roof = Column(String, nullable=True)
    sunroof = Column(String, nullable=True)
    fog_lights = Column(String, nullable=True)
    electric_mirrors = Column(String, nullable=True)
    alarm = Column(String, nullable=True)
    central_lock = Column(String, nullable=True)
    remote_unlock = Column(String, nullable=True)
    airbag = Column(String, nullable=True)
    abs = Column(String, nullable=True)
    electronic_stability = Column(String, nullable=True)
    dpf_fap_filter = Column(String, nullable=True)
    power_steering = Column(String, nullable=True)
    turbo = Column(String, nullable=True)
    isofix = Column(String, nullable=True)
    tow_hook = Column(String, nullable=True)
    customs_cleared = Column(String, nullable=True)
    foreign_license_plates = Column(String, nullable=True)
    on_lease = Column(String, nullable=True)
    service_history = Column(String, nullable=True)
    damaged = Column(String, nullable=True)
    disabled_accessible = Column(String, nullable=True)
    oldtimer = Column(String, nullable=True)

    # relationships
    listings = relationship(
        "ListingModel",
        back_populates="vehicle",
        primaryjoin="VehicleModel.listing_id == ListingModel.listing_id",
        foreign_keys="ListingModel.listing_id",
        overlaps="vehicle",
    )
