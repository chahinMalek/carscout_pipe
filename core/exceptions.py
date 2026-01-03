class PageNotFoundError(Exception):
    """Raised when a page cannot be found during scraping."""

    def __init__(self, url: str):
        self.message = f"Page not found: {url}"
        super().__init__(self.message)
