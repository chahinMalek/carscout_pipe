from logging import DEBUG
from typing import Iterator, List

from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from src.carscout_pipe.core.data_models.brands import Brand
from src.carscout_pipe.core.data_models.listings import Listing
from src.carscout_pipe.core.exceptions import OlxPageNotFound
from src.carscout_pipe.core.scraping.requests import get_page_source, get_next_page
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__, log_level=DEBUG)


def scrape_listings(
        driver: webdriver.Chrome,
        brand: Brand,
        min_delay: int = 1,
        max_delay: int = 5,
        timeout_after: int = 10,
) -> Iterator[List[Listing]]:
    """
    Generator that yields a tuple of (page_url, listing_urls) for each page
    of listings for a brand.
    """
    next_page = "1"
    url_template = (
        "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
        "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
    )

    while next_page:
        url = url_template.format(brand_id=brand.id, page=next_page)
        logger.info(f"Scraping listings from: {url}")

        try:
            articles_page_source = get_page_source(
                driver=driver,
                url=url,
                min_delay=min_delay,
                max_delay=max_delay,
                timeout_after=timeout_after,
            )

            selector = Selector(text=articles_page_source)
            listings_xpath = "//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]"
            listing_cards = selector.xpath(listings_xpath).getall()
            listings = []

            for card in listing_cards:
                card_selector = Selector(text=card)
                listing_url_suffix = card_selector.xpath("//a/@href").get().strip()
                listing_url = f"https://olx.ba{listing_url_suffix}"
                listing_id = listing_url.split("/")[-1]
                title = card_selector.xpath("//a//h1[contains(@class, 'main-heading')]/text()").get().strip()
                price = card_selector.xpath("//a//div[contains(@class, 'price-wrap')]//span[contains(@class, 'smaller')]/text()").get().strip()
                listings.append(Listing(listing_id=listing_id, url=listing_url, title=title, price=price))

            # Yield the current page's data and update for next iteration
            yield listings

            # Get next page for the next iteration
            next_page = get_next_page(articles_page_source)

        except TimeoutException:
            logger.error(f"Error retrieving listings page {url}: Timed out.")
            break
        except OlxPageNotFound:
            logger.error(f"Error retrieving listings page {url}: Not found.")
            break
        except Exception as err:
            logger.error(f"Unexpected error occurred while scraping listings page {url}: {err}")
            break
