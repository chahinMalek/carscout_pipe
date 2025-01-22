"""
This script lets you run a search for each vehicle manufacturer and model and extracts
search results in the first `max_n_pages`.
"""

import json
import requests
from pathlib import Path

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

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
    vehicles_models = vehicles_models.loc[
                      (vehicles_models['Vehicle Name'] == 'Volkswagen'), :]

    # Building request headers
    headers = {'Content-Type': HEADERS_USER_AGENT, 'User-Agent': HEADERS_CONTENT_TYPE,
               'X-Requested-With': 'XMLHttpRequest'}
    query_url = ('https://www.olx.ba/pretraga?vrsta=samoprodaja'
                 '&sort_order=desc&kategorija={kategorija}&v_b={v_b}'
                 '&v_m={v_m}&stranica={stranica}&json=da')
    parser = SearchResultItemParser()

    # Main loop
    results = []

    pbar = tqdm(total=len(vehicles_models), desc='Running the search',
                position=0, ncols=100)
    for row_idx, row in vehicles_models.iterrows():
        pages = range(1, max_n_pages + 1)
        nested_pbar = tqdm(total=len(pages), desc='Searching pages',
                           leave=False, position=1, ncols=100)
        for page in pages:
            search_params = {'v_b': row['Vehicle ID'], 'v_m': row['Model ID'],
                             'stranica': str(page), 'kategorija': ID_CATEGORY_VEHICLES}
            response = requests.get(query_url.format(**search_params),
                                    headers=headers)

            try:
                # HTML parsing the response
                soup = BeautifulSoup(response.json()['rezultati'], features='html.parser')
                page_results = soup.find_all('div',
                                             id=lambda item_id: item_id is not None and item_id.startswith('art_'))
            except requests.exceptions.JSONDecodeError:
                page_results = None

            if page_results is None or len(page_results) == 0:
                nested_pbar.update(max_n_pages - page)
                break
            for res in map(parser.parse, page_results):
                res['Vehicle ID'] = search_params['v_b']
                res['Model ID'] = search_params['v_m']
                results.append(res)
            nested_pbar.update(1)
        nested_pbar.reset()
        pbar.update(1)

    results_parsed = pd.DataFrame(results)
    pd.DataFrame(results_parsed).to_csv(f'./data/results_category={ID_CATEGORY_VEHICLES}.csv')
