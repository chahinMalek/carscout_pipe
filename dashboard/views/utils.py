def format_column_name(col: str) -> str:
    return " ".join(c.capitalize() for c in col.split("_"))
