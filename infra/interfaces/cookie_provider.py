from typing import Protocol


class CookieProvider(Protocol):
    """Provides cookies for HTTP requests."""

    def provide(self, url: str) -> list[dict]:
        """
        Provides cookies for the given URL.

        Args:
            url: The URL to provide cookies from

        Returns:
            List of cookie dictionaries with 'name' and 'value' keys
        """
        ...
