from dataclasses import dataclass


@dataclass(frozen=True)
class Brand:
    id: int
    name: str
    slug: str
