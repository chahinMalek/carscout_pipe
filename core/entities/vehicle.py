import datetime
from dataclasses import dataclass, fields


@dataclass
class Vehicle:
    # listing fields
    id: str
    url: str
    title: str
    price: str
    last_visited_at: datetime.datetime | None = None

    # basic vehicle information
    location: str | None = None
    state: str | None = None
    brand: str | None = None
    model: str | None = None
    fuel_type: str | None = None
    build_year: int | None = None
    mileage: str | None = None
    engine_volume: str | None = None
    engine_power: int | None = None
    num_doors: str | None = None
    transmission: str | None = None
    image_url: str | None = None

    # extended vehicle details
    horsepower: int | None = None
    weight_kg: int | None = None
    vehicle_type: str | None = None
    climate: str | None = None
    audio: str | None = None
    parking_sensors: str | None = None
    parking_camera: str | None = None
    drivetrain: str | None = None
    year_first_registered: int | None = None
    registered_until: str | None = None
    color: str | None = None
    gears: str | None = None
    tyres: str | None = None
    emission: str | None = None
    interior: str | None = None
    curtains: str | None = None
    lights: str | None = None
    number_of_seats: str | None = None
    rim_size: str | None = None
    warranty: str | None = None
    security: str | None = None
    previous_owners: str | None = None
    published_at: datetime.datetime | None = None

    # boolean fields
    registered: bool | None = None
    metallic: bool | None = None
    alloy_wheels: bool | None = None
    digital_air_conditioning: bool | None = None
    steering_wheel_controls: bool | None = None
    navigation: bool | None = None
    touch_screen: bool | None = None
    heads_up_display: bool | None = None
    usb_port: bool | None = None
    cruise_control: bool | None = None
    bluetooth: bool | None = None
    car_play: bool | None = None
    rain_sensor: bool | None = None
    park_assist: bool | None = None
    automatic_light_sensor: bool | None = None
    blind_spot_sensor: bool | None = None
    start_stop_system: bool | None = None
    hill_assist: bool | None = None
    seat_memory: bool | None = None
    seat_massage: bool | None = None
    seat_heating: bool | None = None
    seat_cooling: bool | None = None
    electric_windows: bool | None = None
    electric_seat_adjustment: bool | None = None
    armrest: bool | None = None
    panoramic_roof: bool | None = None
    sunroof: bool | None = None
    fog_lights: bool | None = None
    electric_mirrors: bool | None = None
    alarm: bool | None = None
    central_lock: bool | None = None
    remote_unlock: bool | None = None
    airbag: bool | None = None
    abs: bool | None = None
    electronic_stability: bool | None = None
    dpf_fap_filter: bool | None = None
    power_steering: bool | None = None
    turbo: bool | None = None
    isofix: bool | None = None
    tow_hook: bool | None = None
    customs_cleared: bool | None = None
    foreign_license_plates: bool | None = None
    on_lease: bool | None = None
    service_history: bool | None = None
    damaged: bool | None = None
    disabled_accessible: bool | None = None
    oldtimer: bool | None = None

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, str):
                setattr(self, field.name, value.strip())
        if isinstance(self.build_year, str):
            self.build_year = int(self.build_year)
        if isinstance(self.engine_power, str):
            self.engine_power = int(self.engine_power)
        if isinstance(self.horsepower, str):
            self.horsepower = int(self.horsepower)
        if isinstance(self.weight_kg, str):
            self.weight_kg = int(self.weight_kg.replace(",", "").replace(".", ""))
        if isinstance(self.year_first_registered, str):
            self.year_first_registered = int(self.year_first_registered)
        if isinstance(self.published_at, str):
            self.published_at = datetime.datetime.fromisoformat(self.published_at)
        if isinstance(self.last_visited_at, str):
            self.last_visited_at = datetime.datetime.fromisoformat(self.last_visited_at)

    @classmethod
    def from_dict(cls, data: dict) -> "Vehicle":
        field_names = {f.name for f in fields(cls)}
        _d = {k: v for k, v in data.items() if k in field_names}
        return cls(**_d)

    def timedelta_since_visit(self) -> datetime.timedelta | None:
        if self.last_visited_at is None:
            return None
        return datetime.datetime.now() - self.last_visited_at
