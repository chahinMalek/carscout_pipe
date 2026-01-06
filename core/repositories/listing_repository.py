import datetime
from typing import Protocol

from core.entities.listing import Listing


class ListingRepository(Protocol):
    def add(self, listing: Listing) -> Listing: ...

    def exists(self, id: str) -> bool: ...

    def find_latest(self, id: str) -> Listing | None: ...

    def find_all(self, id: str) -> list[Listing]: ...

    def find_latest_run(self) -> str | None: ...

    def find_without_vehicle_by_run_id(self, run_id: str) -> list[Listing]: ...

    def search_with_run_id(self, run_id: str) -> list[Listing]: ...

    def search(
        self,
        listing_id: str | None = None,
        title: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        min_date: datetime.datetime | None = None,
        max_date: datetime.datetime | None = None,
        run_id: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Listing], int]: ...

    def get_unique_run_ids(self) -> list[str]: ...
