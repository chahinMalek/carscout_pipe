import datetime
from typing import Protocol

from core.entities.listing import Listing


class ListingRepository(Protocol):

    def add(self, listing: Listing) -> Listing:
        ...

    def exists(self, id: str) -> bool:
        ...

    def find_latest(self, id: str) -> Listing | None:
        ...

    def find_all(self, id: str) -> list[Listing]:
        ...

    def search_at(self, date: datetime.datetime) -> list[Listing]:
        ...

    def search_between(self, date_from: datetime.datetime, date_to: datetime.datetime) -> list[Listing]:
        ...
