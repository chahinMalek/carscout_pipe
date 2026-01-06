import datetime
from typing import Protocol

from core.entities.vehicle import Vehicle


class VehicleRepository(Protocol):
    def add(self, vehicle: Vehicle) -> Vehicle: ...

    def exists(self, id: str) -> bool: ...

    def get(self, id: str) -> Vehicle: ...

    def search(
        self,
        listing_id: str | None = None,
        title: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_date: datetime.datetime | None = None,
        max_date: datetime.datetime | None = None,
        brand: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Vehicle], int]: ...

    def get_unique_brands(self) -> list[str]: ...
