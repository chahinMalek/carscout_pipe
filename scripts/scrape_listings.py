import argparse
from pathlib import Path

import pandas as pd

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.scrapers.listings import ListingsScraper


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Scrapes car listings from olx.ba for given brands and models.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--run-id', type=str, required=True,
                       help='Process run identifier.')
    parser.add_argument('--batch-id', type=str, required=True,
                       help='Batch/chunk identifier.')
    parser.add_argument('--config', type=str, default='configs/local.yml',
                       help='Path to the YAML configuration file to load.')
    parser.add_argument('--max-pages', type=int, default=20,
                       help='Maximum number of pages to scrape per brand/model combination.')
    args = parser.parse_args()

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()

    # Read input data
    input_path = Path(config_manager.brands_and_models_path) / args.run_id / f"{args.batch_id}.parquet"
    if not file_service.file_exists(input_path):
        raise ValueError(f"Input file not found at {input_path}")
    
    brands_and_models = file_service.read_parquet(input_path)
    brands_and_models = brands_and_models.to_dict("records")

    # Prepare output directory
    output_dir = Path(config_manager.listings_path) / args.run_id
    file_service.make_directory(output_dir, parents=True)

    try:
        # Initialize and run scraper
        scraper = ListingsScraper(config_manager, file_service, max_pages=args.max_pages)
        listings_data = scraper.scrape(brands_and_models)
        
        # Convert to DataFrame and save
        listings_df = pd.DataFrame(listings_data)
        output_path = output_dir / f"{args.batch_id}.parquet"
        file_service.write_parquet(listings_df, output_path, index=False)

        print("Process finished successfully.")
        
    except Exception as err:
        print("Unexpected error occurred while scraping listings.")
        print(err)
        raise
