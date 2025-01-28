import argparse
from pathlib import Path
import pandas as pd

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.scrapers.vehicles import VehicleScraper


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape vehicle information from listings')
    parser.add_argument('--run-id', required=True, help='Run ID for input/output paths')
    parser.add_argument('--batch-id', required=True, help='Batch ID for input/output files')
    parser.add_argument('--config', type=str, default='configs/local.yml',
                       help='Path to the YAML configuration file to load.')
    args = parser.parse_args()

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()

    # Read input data
    input_path = Path(config_manager.listings_path) / args.run_id / f"{args.batch_id}.parquet"
    if not file_service.file_exists(input_path):
        raise ValueError(f"Input file not found at {input_path}")
    
    # Load and prepare inputs
    listings = file_service.read_parquet(input_path)
    listings = listings.drop_duplicates(ignore_index=True)
    listings = listings.to_dict("records")

    # Configure output path
    output_dir = Path(config_manager.vehicles_path) / args.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.batch_id}.parquet"

    # Scrape vehicles from listings information
    try:
        scraper = VehicleScraper(config_manager, file_service)
        vehicles = scraper.scrape(listings)
        if vehicles:
            output_data = pd.DataFrame(vehicles)
            output_data = output_data.astype(str)
            output_data.to_parquet(output_path, index=False)
    except Exception as err:
        print("Unexpected error occurred while scraping vehicles.")
        print(err)
        raise
