
def parse_price_str(price_str: str) -> tuple[float, str] | None:
    """
    Parses the price string and returns a tuple of (amount, currency) if possible.
    Returns None otherwise.
    """
    _price = price_str.strip().lower()
    if _price in ["na upit", "na", ""]:
        return None
    _price = _price.replace(".", "").replace(",", ".")
    parts = _price.split(" ")
    if len(parts) != 2:
        return None
    try:
        amount = float(parts[0])
        currency = parts[1]
        return amount, currency.upper()
    except ValueError:
        return None
