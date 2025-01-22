import argparse
import uuid
from pathlib import Path

import pandas as pd

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.scrapers.brands_models import BrandsAndModelsScraper


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Scrapes car brands and models data from olx.ba. '
                    'The script collects information about car brands and their corresponding models, '
                    'saving the results to a CSV file. Each run generates a unique ID unless specified.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--run-id', type=str,
                        help='Unique identifier for this scraping run. If not provided, '
                             'a random UUID will be generated.')
    parser.add_argument('--brands', type=str, required=True,
                        help='Path to CSV file containing list of car brands to scrape.')
    parser.add_argument('--config', type=str, default='configs/local.yml',
                        help='Path to the YAML configuration file to load.')
    parser.add_argument('--chunk-size', type=int, default=100,
                        help='Number of items to store in each output chunk.')
    args = parser.parse_args()

    # Initialize services and scraper
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()
    scraper = BrandsAndModelsScraper(config_manager, file_service)
    
    # Setup paths and validate inputs
    run_id = args.run_id if args.run_id else str(uuid.uuid4())
    brands_path = Path(args.brands)
    if not file_service.file_exists(brands_path):
        raise ValueError(f"Brands file not found at {brands_path}")
    
    # Read brands and create output directory
    brands = file_service.read_lines(brands_path)
    output_dir = Path(config_manager.brands_and_models_path) / run_id
    file_service.make_directory(output_dir, parents=True)

    # Scrape, process and save data
    brands_and_models_data = scraper.scrape(brands)
    brands_and_models_df = pd.DataFrame(brands_and_models_data)
    brands_and_models_df = brands_and_models_df.sample(frac=1, random_state=42, ignore_index=True)
    scraper.save_chunks(brands_and_models_df, output_dir, args.chunk_size)
    
    print("Process finished successfully.")
