import datetime
from typing import Protocol

from core.entities.vehicle import Vehicle


class VehicleRepository(Protocol):

    def add(self, vehicle: Vehicle) -> Vehicle:
        ...

    def exists(self, id: str) -> bool:
        ...

    def get(self, id: str) -> Vehicle:
        ...

    def update_last_visited(self, vehicle: Vehicle) -> Vehicle:
        ...
