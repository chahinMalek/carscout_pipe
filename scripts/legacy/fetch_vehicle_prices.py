"""
This script lets you run a search for each vehicle manufacturer and model and extracts
search results in the first `max_n_pages`.
"""

import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from core.parsers.olx_vehicle_search_results import SearchResultItemParser
from config import ID_CATEGORY_VEHICLES, HEADERS_USER_AGENT, HEADERS_CONTENT_TYPE


if __name__ == '__main__':

    # Parameters: 
    # v_b - Internal server ID of a vehicle (how to extract this dynamically?)
    # v_m - Internal server ID of a vehicle model (how to extract this dynamically?)
    # stranica - Page number.
    # kategorija - Category of search - 18 is for vehicles.

    # Read inputs (vehicles and models)
    max_n_pages = 20
    vehicles_models_input_path = f'./data/category={ID_CATEGORY_VEHICLES}.csv'
    vehicles_models = pd.read_csv(vehicles_models_input_path)

    # Building request headers
    headers = {'Content-Type': HEADERS_USER_AGENT, 'User-Agent': HEADERS_CONTENT_TYPE}
    query_url = 'https://www.olx.ba/pretraga?kategorija={kategorija}&v_b={v_b}&v_m={v_m}&stranica={stranica}'
    parser = SearchResultItemParser()
    search_params = {'kategorija': ID_CATEGORY_VEHICLES}

    # Main loop
    pbar = tqdm(total=len(vehicles_models), desc='Running the search')
    for row_idx, row in vehicles_models.iterrows():
        results = []
        pages = range(1, max_n_pages + 1)
        search_params.update({'v_b': row['Vehicle ID'], 'v_m': row['Model ID']})

        # Make sure to create an output path locally
        results_output_path = Path('./data/category={kategorija}/v_b={v_b}/v_m={v_m}.csv'.format(**search_params))
        results_output_path.parents[0].mkdir(parents=True, exist_ok=True)

        for page in pages:
            # Running the request
            search_params.update({'stranica': page})
            response = requests.get(
                query_url.format(**search_params),
                headers=headers
            )
            # HTML parsing the response
            soup = BeautifulSoup(response.text, features='html.parser')
            # Extracting articles
            search_result_items = soup.find_all('div', {'class': 'artikal'})
            if len(search_result_items) == 0:
                break
            # Parsing search result items
            for result_item in search_result_items:
                # Skipping Ads from the result setr
                if 'oglas' in result_item.find('div', {'class': 'naslov'})['class']:
                    continue
                results.append(parser.parse(result_item))
        
        pd.DataFrame.from_records(results).to_csv(results_output_path, index=False)
        pbar.update(1)

    print('Process finished successfully!')
