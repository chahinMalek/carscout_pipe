from typing import Optional, Dict

from pydantic import BaseModel


class Vehicle(BaseModel):
    title: str
    price: float | None = None
    url: str
    location: str
    state: str
    article_id: str
    brand: str
    model: str
    fuel_type: str
    build_year: int
    mileage: int
    engine_volume: str
    engine_power: str
    num_doors: str
    transmission: str
    image_url: Optional[str] = None
    specs: Optional[Dict] = None
