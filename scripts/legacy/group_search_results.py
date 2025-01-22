import pandas as pd
from pathlib import Path


if __name__ == '__main__':
    path_to_partitions = Path('./data/category=18/')
    if not path_to_partitions.exists():
        raise FileNotFoundError('No files found!')
    dfs = []
    for manufacturer_search_results_path in path_to_partitions.iterdir():
        for vehicle_search_results_path in manufacturer_search_results_path.iterdir():
            try:
                manufacturer_id = vehicle_search_results_path.parent.stem[vehicle_search_results_path.parent.stem.find('=') + 1:]
                vehicle_id = vehicle_search_results_path.stem[vehicle_search_results_path.stem.find('=') + 1:]
                df = pd.read_csv(vehicle_search_results_path)
                df['Manufacturer ID'] = manufacturer_id
                df['Vehicle ID'] = vehicle_id
                dfs.append(df)
            except pd.errors.EmptyDataError:
                continue
    full_df = pd.concat(dfs, axis=0, ignore_index=True)
    full_df.to_csv('./data/category=18_all.csv', index=False)
