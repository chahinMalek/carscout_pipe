from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    url: str
    title: str
    price: str
