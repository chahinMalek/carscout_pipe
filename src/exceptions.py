
class VehiclePageNotFound(Exception):
    """Exception raised for vehicle page not found."""

    def __init__(self, url: str):
        self.message = f"Vehicle page not found: {url}"
        super().__init__(self.message)
