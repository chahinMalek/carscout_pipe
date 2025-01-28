import argparse
from pathlib import Path
from datetime import datetime

from pymongo import MongoClient

from src.config import ConfigManager
from src.io.file_service import LocalFileService


if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Ingest scraped vehicles into the database.')
    parser.add_argument('--run-id', required=True, help='Run ID for input/output paths')
    args = parser.parse_args()

    # Initialize services
    file_service = LocalFileService()
    config_manager = ConfigManager.from_local()

    db_params = config_manager.db_connection_params
    client = MongoClient(db_params["host"])
    db = client[db_params["database"]]
    collection = db[config_manager.db_collections["vehicles"]]

    # Read input data
    input_path = Path(config_manager.vehicles_path) / args.run_id
    if not file_service.directory_exists(input_path):
        raise ValueError(f"Input file not found at {input_path}")
    
    vehicles = file_service.read_parquet(input_path)
    vehicles = vehicles.to_dict("records")

    # Retrieve existing URLs from the database
    existing_urls = set(collection.distinct("url"))
    print(f"Retrieved {len(existing_urls)} existing URLs from the database.")

    # Process each Parquet file
    for partfile in input_path.glob("*.parquet"):
        print(f"Processing file: {partfile}")

        # Read Parquet file into a DataFrame
        df = file_service.read_parquet(partfile)
        df["specs"] = df["specs"].apply(lambda s: eval(s))
        df = df.loc[~df["url"].isin(existing_urls)]
        df = df.reset_index(drop=True)
        df["ingested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records = df.to_dict(orient="records")

        # Insert records into MongoDB collection
        if records:
            collection.insert_many(records)
            print(f"Inserted {len(records)} records from {partfile} into MongoDB.")

    print("All part files have been successfully added to the database.")
