"""
This script lets you fetch all vehicles manufacturers and models from https://www.olx.ba/
and saves the results as a convenient CSV file.
"""

import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from config import HEADERS_CONTENT_TYPE, HEADERS_USER_AGENT, ID_CATEGORY_VEHICLES


if __name__ == '__main__':

    # Parameters: 
    # kategorija - Category of search - 18 is for vehicles.
    search_params = {'kategorija': ID_CATEGORY_VEHICLES}

    # Make sure to create an output path locally
    results_output_path = Path('./data/category={kategorija}.csv'.format(**search_params))
    results_output_path.parents[0].mkdir(parents=True, exist_ok=True)

    # Building request headers
    headers = {'Content-Type': HEADERS_CONTENT_TYPE, 'User-Agent': HEADERS_USER_AGENT}
    query_vehicles_url = 'https://www.olx.ba/vozila'
    query_vehicle_models_url = 'https://www.olx.ba/ajax/vozilamodeli/{vehicle_id}'
    results = []

    # HTML parsing the vehicles response
    vehicles_response = requests.get(
        query_vehicles_url.format(**search_params),
        headers=headers
    )
    vehicles_soup = BeautifulSoup(vehicles_response.text, features='html.parser')
    vehicle_dropdown_container = vehicles_soup.find('div', {'class': 'drop-container', 'id': 'proizvodjac-drop'})
    vehicle_dropdown = vehicle_dropdown_container.find('select', {'id': 'v_b', 'name': 'v_b'})

    # Main loop
    pbar = tqdm(total=len(vehicle_dropdown.find_all('option')), desc='Executing search')
    for vehicle_item in vehicle_dropdown.find_all('option'):
        if vehicle_item['value'] == '':
            continue
        vehicle_name = vehicle_item.get_text().split('(')[0].strip()
        vehicle_id = vehicle_item['value']

        # Searching for vehicle models
        vehicle_models_response = requests.get(
            query_vehicle_models_url.format(vehicle_id=vehicle_id),
            headers=headers
        )
        vehicle_models_soup = BeautifulSoup(vehicle_models_response.text, features='html.parser')
        vehicle_models = vehicle_models_soup.find('select', {'id': 'v_m', 'name': 'v_m'})
        for vehicle_model in vehicle_models.find_all('option'):
            if vehicle_model['value'] == '' or ',' in vehicle_model['value']:
                continue
            res = {
                'Vehicle Name': vehicle_name,
                'Vehicle ID': vehicle_id,
                'Model ID': vehicle_model['value'],
                'Model Name': vehicle_model.get_text().replace('&nbsp', '').strip()
            }
            results.append(res)
        pbar.update(1)

    print('Saving results ...')
    pd.DataFrame.from_records(results).groupby(
        by=['Vehicle Name', 'Vehicle ID', 'Model ID']
        ).first().reset_index().to_csv(results_output_path, index=False)
    print('Process finished successfully!')
