import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime
from typing import Dict

import pandas as pd
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache, private",
    "Sec-Ch-Ua": '"Not A(Brand";v="8", "Chromium";v="132", "Brave";v="132"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOs"',
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en;q=0.9"
}

def init_driver():
    logger.debug("Initializing WebDriver")
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver


def get_next_page(page_source: str):
    logger.debug("Retrieving next page ...")
    selector = Selector(text=page_source)
    pagination_item = selector.xpath("//div[@class='olx-pagination-wrapper']").get()
    if not pagination_item:
        logger.debug("No pagination item found")
        return None
    next_page_xpath = "normalize-space(//li[@class='active']/following-sibling::li[1]/text())"
    next_page = Selector(text=pagination_item).xpath(next_page_xpath).get()
    next_page = next_page or None
    logger.debug(f"Next page: {next_page}")
    return next_page


def parse_vehicle_info(selector: Selector) -> Dict:
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
        "horsepower": "//div//table//td[normalize-space(text())='Konjskih snaga']/following-sibling::td[1]//text()",
        "weight_kg": "//div//table//td[normalize-space(text())='Masa/Težina (kg)']/following-sibling::td[1]//text()",
        "vehicle_type": "//div//table//td[normalize-space(text())='Tip']/following-sibling::td[1]//text()",
        "climate": "//div//table//td[normalize-space(text())='Klimatizacija']/following-sibling::td[1]//text()",
        "audio": "//div//table//td[normalize-space(text())='Muzika/ozvučenje']/following-sibling::td[1]//text()",
        "parking_sensors": "//div//table//td[normalize-space(text())='Parking senzori']/following-sibling::td[1]//text()",
        "parking_camera": "//div//table//td[normalize-space(text())='Parking kamera']/following-sibling::td[1]//text()",
        "drivetrain": "//div//table//td[normalize-space(text())='Pogon']/following-sibling::td[1]//text()",
        "year_first_registered": "//div//table//td[normalize-space(text())='Godina prve registracije']/following-sibling::td[1]//text()",
        "registered_until": "//div//table//td[normalize-space(text())='Registrovan do']/following-sibling::td[1]//text()",
        "color": "//div//table//td[normalize-space(text())='Boja']/following-sibling::td[1]//text()",
        "gears": "//div//table//td[normalize-space(text())='Broj stepeni prijenosa']/following-sibling::td[1]//text()",
        "tyres": "//div//table//td[normalize-space(text())='Posjeduje gume']/following-sibling::td[1]//text()",
        "emission": "//div//table//td[normalize-space(text())='Emisioni standard']/following-sibling::td[1]//text()",
        "interior": "//div//table//td[normalize-space(text())='Vrsta enterijera']/following-sibling::td[1]//text()",
        "curtains": "//div//table//td[normalize-space(text())='Rolo zavjese']/following-sibling::td[1]//text()",
        "lights": "//div//table//td[normalize-space(text())='Svjetla']/following-sibling::td[1]//text()",
        "number_of_seats": "//div//table//td[normalize-space(text())='Sjedećih mjesta']/following-sibling::td[1]//text()",
        "rim_size": "//div//table//td[normalize-space(text())='Veličina felgi']/following-sibling::td[1]//text()",
        "warranty": "//div//table//td[normalize-space(text())='Garancija']/following-sibling::td[1]//text()",
        "security": "//div//table//td[normalize-space(text())='Zaštita/Blokada']/following-sibling::td[1]//text()",
        "previous_owners": "//div//table//td[normalize-space(text())='Broj prethodnih vlasnika']/following-sibling::td[1]//text()",
        "published_at": "//div//table//td[normalize-space(text())='Datum objave']/following-sibling::td[1]//text()",
        "registered": "//div//table//td[normalize-space(text())='Registrovan']/following-sibling::td[1]",
        "metallic": "//div//table//td[normalize-space(text())='Metalik']/following-sibling::td[1]",
        "alloy_wheels": "//div//table//td[normalize-space(text())='Alu felge']/following-sibling::td[1]",
        "digital_air_conditioning": "//div//table//td[normalize-space(text())='Digitalna klima']/following-sibling::td[1]",
        "steering_wheel_controls": "//div//table//td[normalize-space(text())='Komande na volanu']/following-sibling::td[1]",
        "navigation": "//div//table//td[normalize-space(text())='Navigacija']/following-sibling::td[1]",
        "touch_screen": "//div//table//td[normalize-space(text())='Touch screen (ekran)']/following-sibling::td[1]",
        "heads_up_display": "//div//table//td[normalize-space(text())='Head up display']/following-sibling::td[1]",
        "usb_port": "//div//table//td[normalize-space(text())='USB port']/following-sibling::td[1]",
        "cruise_control": "//div//table//td[normalize-space(text())='Tempomat']/following-sibling::td[1]",
        "bluetooth": "//div//table//td[normalize-space(text())='Bluetooth']/following-sibling::td[1]",
        "car_play": "//div//table//td[normalize-space(text())='Car play']/following-sibling::td[1]",
        "rain_sensor": "//div//table//td[normalize-space(text())='Senzor kiše']/following-sibling::td[1]",
        "park_assist": "//div//table//td[normalize-space(text())='Park assist']/following-sibling::td[1]",
        "automatic_light_sensor": "//div//table//td[normalize-space(text())='Senzor auto. svjetla']/following-sibling::td[1]",
        "blind_spot_sensor": "//div//table//td[normalize-space(text())='Senzor mrtvog ugla']/following-sibling::td[1]",
        "start_stop_system": "//div//table//td[normalize-space(text())='Start-Stop sistem']/following-sibling::td[1]",
        "hill_assist": "//div//table//td[normalize-space(text())='Hill assist']/following-sibling::td[1]",
        "seat_memory": "//div//table//td[normalize-space(text())='Memorija sjedišta']/following-sibling::td[1]",
        "seat_massage": "//div//table//td[normalize-space(text())='Masaža sjedišta']/following-sibling::td[1]",
        "seat_heating": "//div//table//td[normalize-space(text())='Grijanje sjedišta']/following-sibling::td[1]",
        "seat_cooling": "//div//table//td[normalize-space(text())='Hlađenje sjedišta']/following-sibling::td[1]",
        "electric_windows": "//div//table//td[normalize-space(text())='El. podizači stakala']/following-sibling::td[1]",
        "electric_seat_adjustment": "//div//table//td[normalize-space(text())='El. pomjeranje sjedišta']/following-sibling::td[1]",
        "armrest": "//div//table//td[normalize-space(text())='Naslon za ruku']/following-sibling::td[1]",
        "panoramic_roof": "//div//table//td[normalize-space(text())='Panorama krov']/following-sibling::td[1]",
        "sunroof": "//div//table//td[normalize-space(text())='Šiber']/following-sibling::td[1]",
        "fog_lights": "//div//table//td[normalize-space(text())='Maglenke']/following-sibling::td[1]",
        "electric_mirrors": "//div//table//td[normalize-space(text())='Električni retrovizori']/following-sibling::td[1]",
        "alarm": "//div//table//td[normalize-space(text())='Alarm']/following-sibling::td[1]",
        "central_lock": "//div//table//td[normalize-space(text())='Centralna brava']/following-sibling::td[1]",
        "remote_unlock": "//div//table//td[normalize-space(text())='Daljinsko otključavanje']/following-sibling::td[1]",
        "airbag": "//div//table//td[normalize-space(text())='Airbag']/following-sibling::td[1]",
        "abs": "//div//table//td[normalize-space(text())='ABS']/following-sibling::td[1]",
        "electronic_stability": "//div//table//td[normalize-space(text())='ESP']/following-sibling::td[1]",
        "dpf_fap_filter": "//div//table//td[normalize-space(text())='DPF/FAP filter']/following-sibling::td[1]",
        "power_steering": "//div//table//td[normalize-space(text())='Servo volan']/following-sibling::td[1]",
        "turbo": "//div//table//td[normalize-space(text())='Turbo']/following-sibling::td[1]",
        "isofix": "//div//table//td[normalize-space(text())='ISOFIX']/following-sibling::td[1]",
        "tow_hook": "//div//table//td[normalize-space(text())='Auto kuka']/following-sibling::td[1]",
        "customs_cleared": "//div//table//td[normalize-space(text())='Ocarinjen']/following-sibling::td[1]",
        "foreign_license_plates": "//div//table//td[normalize-space(text())='Strane tablice']/following-sibling::td[1]",
        "on_lease": "//div//table//td[normalize-space(text())='Na lizingu']/following-sibling::td[1]",
        "service_history": "//div//table//td[normalize-space(text())='Servisna knjiga']/following-sibling::td[1]",
        "damaged": "//div//table//td[normalize-space(text())='Udaren']/following-sibling::td[1]",
        "disabled_accessible": "//div//table//td[normalize-space(text())='Prilagođen invalidima']/following-sibling::td[1]",
        "oldtimer": "//div//table//td[normalize-space(text())='Oldtimer']/following-sibling::td[1]",
    }

    params = {}
    for attribute, xpath in xpaths.items():
        value = selector.xpath(xpath).get()
        if not xpath.endswith("text()"):
            value = True if value else False
        elif isinstance(value, str):
            value = value.strip()
        params[attribute] = value

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

    if params["published_at"]:
        params["published_at"] = datetime.strptime(params["published_at"], "%d.%m.%Y").strftime("%Y-%m-%d")

    return params


if __name__ == '__main__':

    brands_path = "../data/brands.csv"
    logger.debug(f"{brands_path=}")
    brands = pd.read_csv(brands_path).to_dict(orient="records")

    driver = init_driver()
    url_template = (
        "https://olx.ba/pretraga?attr=&attr_encoded=1&category_id=18&"
        "brand={brand_id}&models=0&brands={brand_id}&page={page}&created_gte=-7+days"
    )

    request_min_delay_seconds = 1
    request_max_delay_seconds = 4
    wait_time_seconds = 10
    run_id = str(uuid.uuid4())

    logger.debug(f"{request_min_delay_seconds=}")
    logger.debug(f"{request_max_delay_seconds=}")
    logger.debug(f"{wait_time_seconds=}")
    logger.debug(f"{run_id=}")

    output_dir = f"../data/output/{run_id}/"
    os.makedirs(output_dir, exist_ok=True)
    filename_template = "part_{idx:08}.csv"
    output_partfile_template = os.path.join(output_dir, filename_template)
    global_idx = 0

    for brand_data in brands:
        brand_id = brand_data["brand_id"]
        next_page = "1"

        while next_page:
            url = url_template.format(brand_id=brand_id, page=next_page)
            logger.info(f"Scraping listings from: {url}")

            try:
                request_delay = random.uniform(request_min_delay_seconds, request_max_delay_seconds)
                time.sleep(request_delay)
                driver.get(url)
                WebDriverWait(driver, wait_time_seconds).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "articles"))
                )
                articles_page_source = driver.page_source
                selector = Selector(text=articles_page_source)
            except Exception as err:
                logger.error(f"Error occurred while scraping page: {err}")
                break
            logger.debug("Listings page retrieved successfully.")

            try:
                listing_urls_xpath = "//div[contains(@class, 'articles')]//div[contains(@class, 'cardd')]//a/@href"
                listing_urls = selector.xpath(listing_urls_xpath).getall()
                logger.debug(f"{len(listing_urls)=}")
                listing_urls = [f"https://olx.ba{url_suffix}" for url_suffix in listing_urls]
                random.shuffle(listing_urls)
            except Exception as err:
                logger.error(f"Error occurred while parsing listing URLs: {err}")
                break
            logger.debug("Listings retrieved successfully.")

            vehicles = []
            pbar = tqdm(listing_urls, desc=f"Processing listings", file=open(os.devnull, 'w'))
            for listing_url in pbar:
                request_delay = random.uniform(request_min_delay_seconds, request_max_delay_seconds)
                try:
                    time.sleep(request_delay)
                    driver.get(listing_url)
                    WebDriverWait(driver, wait_time_seconds).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "required-attributes"))
                    )
                    selector = Selector(text=driver.page_source)
                    vehicle = parse_vehicle_info(selector)
                    vehicle["url"] = listing_url
                    vehicle["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    vehicles.append(vehicle)
                except Exception as err:
                    logger.error(f"Error occurred while scraping vehicle: {err}")
                finally:
                    logger.info(str(pbar))
            pbar.close()
            logger.debug("All vehicles from the page retrieved successfully.")

            try:
                output_path = output_partfile_template.format(idx=global_idx)
                logger.debug(f"Saving batch into `{output_path}` ...")
                df = pd.DataFrame(vehicles)
                df.to_csv(output_path, index=False)
                logger.debug(f"Batch saving successful.")
                global_idx += 1
            except Exception as err:
                logger.error(f"Error occurred while saving batch: {err}")

            try:
                next_page = get_next_page(articles_page_source)
            except Exception as err:
                logger.error(f"Error occurred while parsing next page: {err}")
                break
