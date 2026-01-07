import datetime
from typing import TypeAlias

# types
DateRange: TypeAlias = tuple[datetime.datetime | None, datetime.datetime | None]


# utility functions
def format_column_name(col: str) -> str:
    return " ".join(c.capitalize() for c in col.split("_"))


def parse_date_range(date_range: tuple | None) -> DateRange:
    min_date = None
    max_date = None

    if isinstance(date_range, tuple) and len(date_range) > 0:
        min_date = datetime.datetime.combine(date_range[0], datetime.time.min)
        if len(date_range) > 1:
            max_date = datetime.datetime.combine(date_range[1], datetime.time.max)

    return min_date, max_date
