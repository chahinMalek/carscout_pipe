import time
from typing import List, Dict

from backoff import on_exception, expo
from datetime import datetime
from requests import RequestException
from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
from pydantic import ValidationError

from src.config import ConfigManager
from src.io.file_service import LocalFileService
from src.data_models.vehicle import Vehicle
from src.scrapers.selenium_base import SeleniumScraper
from src.exceptions import VehiclePageNotFound


class VehicleScraper(SeleniumScraper):
    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService):
        super().__init__(config_manager, file_service)

    def scrape(self, listings: List[Dict]) -> List[Dict]:
        """Scrape vehicle details from a list of listings"""
        vehicles = []

        for listing in tqdm(listings, desc="Scraping vehicles"):
            try:
                url = listing["url"]
                vehicle = self._parse_vehicle_info(url)
                if vehicle:
                    vehicle_dict = vehicle.model_dump()
                    vehicle_dict["scraped_at"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    vehicles.append(vehicle_dict)
            except TimeoutException:
                print(f"Error retrieving vehicle info from {url}: Timed out.")
            except VehiclePageNotFound as err:
                print(f"Error retrieving vehicle info from {url}: {err}")
            except ValidationError as err:
                print(f"Error parsing vehicle info from {url}: {err}")
            except Exception as err:
                print(f"Unexpected error scraping vehicle info from {url}: {err}")

        self.cleanup()
        return vehicles

    @on_exception(
        expo,
        RequestException,
        max_tries=3,
        max_time=60,
        giveup=lambda e: isinstance(e, VehiclePageNotFound),
    )
    def _parse_vehicle_info(self, url: str) -> Vehicle | None:
        """Parse vehicle info from a given URL"""

        try:
            self.driver.get(url)
            time.sleep(2)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div//h1[contains(@class, 'main-title-listing')]")
                )
            )
            selector = Selector(text=self.driver.page_source)

        except TimeoutException as err:
            if "Oprostite, ne možemo pronaći ovu stranicu" in self.driver.page_source:
                raise VehiclePageNotFound(url)
            raise err  # re-raise the error for backoff

        xpaths = {
            "title": "//div//h1[contains(@class, 'main-title-listing')]/text()",
            "price": "//div//span[contains(@class, 'price-heading')]/text()",
            "location": "//div//label[svg/path[@d='M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z']]/text()",
            "state": "//div//label[svg/path[@d='M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z']]/text()",
            "article_id": "//div//label[svg/path[@d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z']]/text()",
            "brand": "//div//td[normalize-space(text())='Proizvođač']/following-sibling::td[1]//text()",
            "model": "//div//td[normalize-space(text())='Model']/following-sibling::td[1]//text()",
            "fuel_type": "//div//td[normalize-space(text())='Gorivo']/following-sibling::td[1]//text()",
            "build_year": "//div//td[normalize-space(text())='Godište']/following-sibling::td[1]//text()",
            "mileage": "//div//td[normalize-space(text())='Kilometraža']/following-sibling::td[1]//text()",
            "engine_volume": "//div//td[normalize-space(text())='Kubikaža']/following-sibling::td[1]//text()",
            "engine_power": "//div//td[normalize-space(text())='Snaga motora (KW)']/following-sibling::td[1]//text()",
            "num_doors": "//div//td[normalize-space(text())='Broj vrata']/following-sibling::td[1]//text()",
            "transmission": "//div//td[normalize-space(text())='Transmisija']/following-sibling::td[1]//text()",
            "image_url": "//div[@class='main-image-overlay-content']//div[@class='gallery-items']/img[1]/@src",
        }

        params = {"url": url}
        for attribute, xpath in xpaths.items():
            value = selector.xpath(xpath).get()
            if isinstance(value, str):
                value = value.strip()
            params[attribute] = value if value else None

        if params["article_id"]:
            params["article_id"] = (
                params["article_id"].replace("\n", " ").split(": ")[-1].strip()
            )

        if params["price"]:
            if params["price"].lower().strip() == "na upit":
                params["price"] = None
            else:
                price_str = (
                    params["price"].split(" ")[0].replace(".", "").replace("KM", "")
                )
                params["price"] = float(price_str.replace(",", "."))

        if params["mileage"]:
            params["mileage"] = int(
                params["mileage"].split(" ")[0].replace(".", "").replace("km", "")
            )

        if params["build_year"]:
            params["build_year"] = int(params["build_year"])

        specs = {}
        specs_rows_list = []
        specs_rows_list.extend(
            selector.xpath(
                "//div/h2[normalize-space(text())='Specifikacije']/following-sibling::table[1]//tr"
            ).getall()
        )
        specs_rows_list.extend(
            selector.xpath(
                "//div/h2[normalize-space(text())='Oprema']/following-sibling::table[1]//tr"
            ).getall()
        )
        for spec_row in specs_rows_list:
            values = Selector(text=spec_row).xpath("//td//text()").getall()
            if values:
                spec = values[0]
                value = values[1].strip() if len(values) > 1 else True
                specs[spec.strip()] = value

        params["specs"] = specs
        return Vehicle(**params)
