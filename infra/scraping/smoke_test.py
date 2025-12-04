"""
Minimal smoke test for ListingScraper.

Usage:
  python -m infra.scraping.smoke_test "https://example.com" \
    "https://example.com/listings"

It initializes WebDriver, bootstraps an HTTP client via cookies,
fetches the target pages, and prints parsed results.
"""

import sys
from typing import Optional

from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory
from infra.factory.clients.http import HttpClientFactory, ClientType
from infra.scraping.listing_scraper import ListingScraper


def main(argv: list[str]) -> int:
    if not argv:
        print("Provide base_url and optional paths. Example:")
        print("python -m infra.scraping.smoke_test https://example.com /listings /listings?page=2")
        return 2

    base_url = argv[0]
    paths = argv[1:] if len(argv) > 1 else None

    logger_factory = LoggerFactory()
    webdriver_factory = WebdriverFactory(
        chrome_options=["--headless=new", "--no-sandbox", "--disable-gpu"],
        use_stealth=True,
        logger_factory=logger_factory,
    )

    http_client_factory = HttpClientFactory(
        url=base_url,
        headers={"User-Agent": "carscout-pipe/smoke-test"},
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        client_type=ClientType.REQUESTS,
    )

    scraper = ListingScraper(
        base_url=base_url,
        logger_factory=logger_factory,
        webdriver_factory=webdriver_factory,
        http_client_factory=http_client_factory,
    )

    listings = scraper.scrape_listings(paths=paths)
    print(f"Scraped {len(listings)} listings")
    for i, item in enumerate(listings[:10], 1):
        print(f"{i}. {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
