import datetime
from dataclasses import dataclass, fields

from core.utils.prices import parse_price_str


@dataclass
class Listing:
    id: str
    url: str
    title: str
    price: str
    visited_at: datetime.datetime | None = None
    run_id: str | None = None

    def __post_init__(self):
        self.id = self.id.strip()
        self.title = self.title.strip()
        self.url = self.url.strip()
        self.price = self.price.strip()
        if self.run_id:
            self.run_id = self.run_id.strip()
        if isinstance(self.visited_at, str):
            self.visited_at = datetime.datetime.fromisoformat(self.visited_at)

    @classmethod
    def from_dict(cls, data: dict) -> 'Listing':
        field_names = {f.name for f in fields(cls)}
        _d = {k: v for k, v in data.items() if k in field_names}
        return cls(**_d)

    def parsed_price(self) -> tuple[float, str] | None:
        return parse_price_str(self.price)

    def timedelta_since_visit(self) -> datetime.timedelta | None:
        if self.visited_at is None:
            return None
        return datetime.datetime.now() - self.visited_at
