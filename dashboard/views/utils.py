import datetime
from typing import Any, TypeAlias

# types
DateRange: TypeAlias = tuple[datetime.datetime | None, datetime.datetime | None]
FilterParams: TypeAlias = dict[str, Any]


# utility functions
def format_column_name(col: str) -> str:
    """Convert snake_case column name to Title Case."""
    return " ".join(c.capitalize() for c in col.split("_"))


def hash_filter_params(params: FilterParams) -> str:
    """Create a stable string hash from filter parameters."""
    sorted_items = sorted(params.items(), key=lambda x: x[0])
    return "&".join(f"{k}={v}" for k, v in sorted_items)


def parse_date_range(date_range: tuple | None) -> DateRange:
    min_date = None
    max_date = None

    if isinstance(date_range, tuple) and len(date_range) > 0:
        min_date = datetime.datetime.combine(date_range[0], datetime.time.min)
        if len(date_range) > 1:
            max_date = datetime.datetime.combine(date_range[1], datetime.time.max)

    return min_date, max_date
