import uuid
from typing import List

import pandas as pd

from src.carscout_pipe.core.data_models.brands import Brand
from src.carscout_pipe.core.scraping.listings import extract_listings
from src.carscout_pipe.core.scraping.webdriver import init_driver


BRANDS_CSV_PATH = "data/seeds/brands.csv"
RUN_ID = str(uuid.uuid4())


def load_brands() -> List[Brand]:
    """Load brands from CSV file."""
    df = pd.read_csv(BRANDS_CSV_PATH)
    return [Brand(**row) for index, row in df.iterrows()]


def main() -> None:
    brands = load_brands()
    for brand in brands:
        # reinit driver for each brand
        driver = init_driver()
        listings_generator = extract_listings(driver, brand)
        for listings in listings_generator:
            print(listings)



if __name__ == '__main__':
    main()
