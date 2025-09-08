from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    listing_id: str
    url: str
    title: str
    price: str
