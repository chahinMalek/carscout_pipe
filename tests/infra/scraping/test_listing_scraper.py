from unittest.mock import Mock, patch

import pytest

from core.entities.brand import Brand
from core.entities.listing import Listing
from core.exceptions import PageNotFoundError
from infra.factory.webdriver import WebdriverFactory
from infra.scraping.listing_scraper import ListingScraper


@pytest.mark.unit
class TestListingScraper:
    @pytest.fixture
    def mock_webdriver_factory(self):
        return Mock(spec=WebdriverFactory)

    @pytest.fixture
    def mock_driver(self):
        driver = Mock()
        driver.page_source = ""
        driver.execute_script.return_value = "complete"
        return driver

    @pytest.fixture
    def scraper(self, mock_logger_factory, mock_webdriver_factory):
        return ListingScraper(
            logger_factory=mock_logger_factory,
            webdriver_factory=mock_webdriver_factory,
            min_req_delay=1.0,
            max_req_delay=2.0,
            timeout=5.0,
        )

    @pytest.fixture
    def sample_brand(self):
        return Brand(id="123", name="BMW", slug="bmw")

    def test_check_page_unk(self, scraper):
        pages_not_found = [
            "<html>Oprostite, ne možemo pronaći ovu stranicu</html>",
            "<html>Nema rezultata za traženi pojam</html>",
        ]
        for page_source in pages_not_found:
            assert scraper._check_page_unk(page_source) is True

        valid_pages = [
            "<html><body>Valid content here</body></html>",
        ]
        for page_source in valid_pages:
            assert scraper._check_page_unk(page_source) is False

    def test_extract_listings(self, scraper):
        page_source = """
        <html>
            <a href="/artikal/11111">
                <h1 class="main-heading">BMW X5</h1>
                <div class="price-wrap"><span class="smaller">45.000 KM</span></div>
            </a>
            <a href="/artikal/22222">
                <h1 class="main-heading">Audi A4</h1>
                <div class="price-wrap"><span class="smaller">30.000 KM</span></div>
            </a>
            <a href="/artikal/33333">
                <h1 class="main-heading">Mercedes C250</h1>
                <div class="price-wrap"><span class="smaller">35.000 KM</span></div>
            </a>
        </html>
        """
        expected = [
            {
                "id": "11111",
                "url": "https://olx.ba/artikal/11111",
                "title": "BMW X5",
                "price": "45.000 KM",
            },
            {
                "id": "22222",
                "url": "https://olx.ba/artikal/22222",
                "title": "Audi A4",
                "price": "30.000 KM",
            },
            {
                "id": "33333",
                "url": "https://olx.ba/artikal/33333",
                "title": "Mercedes C250",
                "price": "35.000 KM",
            },
        ]
        listings = scraper._extract_listings(page_source)
        assert len(listings) == len(expected)

        for actual, result in zip(expected, listings, strict=False):
            assert result.id == actual["id"]
            assert result.url == actual["url"]
            assert result.title == actual["title"]
            assert result.price == actual["price"]

    def test_extract_listings_empty(self, scraper):
        page_source = "<html><body>No listings here</body></html>"
        listings = scraper._extract_listings(page_source)
        assert len(listings) == 0

    def test_get_next_page(self, scraper):
        inputs = [
            # actual positive case - needs to extract the next page number
            """
            <html>
                <div class="olx-pagination-wrapper">
                    <li class="active">2</li>
                    <li>3</li>
                </div>
            </html>
            """,
            # nothing to extract
            "<html><body>No pagination</body></html>",
            # needs to return None because there's no next page
            """
            <html>
                <div class="olx-pagination-wrapper">
                    <li>4</li>
                    <li class="active">5</li>
                </div>
            </html>
            """,
        ]
        expected_results = ["3", None, None]
        for page_source, expected in zip(inputs, expected_results, strict=False):
            result = scraper._get_next_page(page_source)
            assert result is None and expected is None or result == expected

    def test_get_page_source_returns_html(self, scraper, mock_driver):
        mock_driver.page_source = "<html>Valid content</html>"
        url = "https://olx.ba/test"

        with patch("time.sleep"):
            result = scraper._get_page_source(url, mock_driver)

        assert result == "<html>Valid content</html>"
        mock_driver.get.assert_called_once_with(url)

    def test_get_page_source_raises_page_not_found_error(self, scraper, mock_driver):
        mock_driver.page_source = "Oprostite, ne možemo pronaći ovu stranicu"
        url = "https://olx.ba/test"

        with patch("time.sleep"):
            with pytest.raises(PageNotFoundError):
                scraper._get_page_source(url, mock_driver)

    def test_get_page_source_respects_delay(self, scraper, mock_driver):
        mock_driver.page_source = "<html>Content</html>"
        url = "https://olx.ba/test"

        with patch("time.sleep") as mock_sleep:
            scraper._get_page_source(url, mock_driver)

            mock_sleep.assert_called_once()
            delay_arg = mock_sleep.call_args[0][0]
            assert scraper._min_req_delay <= delay_arg <= scraper._max_req_delay

    def test_scrape_listings_single_page(self, scraper, mock_driver, sample_brand):
        page_html = """
        <html>
            <a href="/artikal/11111">
                <h1 class="main-heading">BMW M3</h1>
                <div class="price-wrap"><span class="smaller">40.000 KM</span></div>
            </a>
        </html>
        """
        mock_driver.page_source = page_html

        with patch.object(scraper, "_get_page_source", return_value=page_html):
            with patch.object(scraper, "_get_next_page", return_value=None):
                listings = list(scraper.scrape_listings(mock_driver, sample_brand))

        assert len(listings) == 1
        assert listings[0].id == "11111"
        assert listings[0].url == "https://olx.ba/artikal/11111"
        assert listings[0].title == "BMW M3"
        assert listings[0].price == "40.000 KM"

    def test_scrape_listings_multiple_pages(self, scraper, mock_driver, sample_brand):
        """Test scraping multiple pages."""
        page1_html = """
        <html>
            <a href="/artikal/11111">
                <h1 class="main-heading">BMW M3</h1>
                <div class="price-wrap"><span class="smaller">40.000 KM</span></div>
            </a>
            <div class="olx-pagination-wrapper"><li class="active">1</li><li>2</li></div>
        </html>
        """
        page2_html = """
        <html>
            <a href="/artikal/22222">
                <h1 class="main-heading">Audi A4</h1>
                <div class="price-wrap"><span class="smaller">30.000 KM</span></div>
            </a>
        </html>
        """

        with patch.object(scraper, "_get_page_source", side_effect=[page1_html, page2_html]):
            listings = list(scraper.scrape_listings(mock_driver, sample_brand))

        assert len(listings) == 2
        assert listings[0].id == "11111"
        assert listings[0].url == "https://olx.ba/artikal/11111"
        assert listings[0].title == "BMW M3"
        assert listings[0].price == "40.000 KM"
        assert listings[1].id == "22222"
        assert listings[1].url == "https://olx.ba/artikal/22222"
        assert listings[1].title == "Audi A4"
        assert listings[1].price == "30.000 KM"

    def test_run_handles_driver_on_success(
        self, scraper, mock_webdriver_factory, mock_driver, sample_brand
    ):
        mock_webdriver_factory.create.return_value = mock_driver

        with patch.object(scraper, "scrape_listings", return_value=iter([])):
            list(scraper.run(sample_brand))

        mock_webdriver_factory.create.assert_called_once()
        mock_driver.quit.assert_called_once()

    def test_run_handles_driver_on_exception(
        self, scraper, mock_webdriver_factory, mock_driver, sample_brand
    ):
        mock_webdriver_factory.create.return_value = mock_driver

        with patch.object(scraper, "scrape_listings", side_effect=Exception("Error")):
            list(scraper.run(sample_brand))

        mock_driver.quit.assert_called_once()

    def test_run_yields_listings(self, scraper, mock_webdriver_factory, mock_driver, sample_brand):
        mock_webdriver_factory.create.return_value = mock_driver
        mock_listings = [
            Listing(
                id="11111", url="https://olx.ba/artikal/11111", title="BMW M3", price="40.000 KM"
            ),
            Listing(
                id="22222", url="https://olx.ba/artikal/22222", title="Audi A4", price="30.000 KM"
            ),
        ]

        with patch.object(scraper, "scrape_listings", return_value=iter(mock_listings)):
            result = list(scraper.run(sample_brand))

        assert len(result) == 2
        assert result[0].id == "11111"
        assert result[0].url == "https://olx.ba/artikal/11111"
        assert result[0].title == "BMW M3"
        assert result[0].price == "40.000 KM"
        assert result[1].id == "22222"
        assert result[1].url == "https://olx.ba/artikal/22222"
        assert result[1].title == "Audi A4"
        assert result[1].price == "30.000 KM"
