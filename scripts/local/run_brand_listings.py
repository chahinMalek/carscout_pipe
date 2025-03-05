import argparse
import multiprocessing
from pathlib import Path

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.brand_listings import ScrapeBrandListingsStep
from src.scrapers.brand_listings import BrandListingsScraper
from src.utils.logging import get_logger


def process_batch(context: StepContext) -> None:
    """Process a single batch with proper error handling."""
    step = ScrapeBrandListingsStep()
    return step.execute(context)


def main():

    parser = argparse.ArgumentParser(
        description="Scrapes car listings from olx.ba for given brands and models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run-id", type=str, required=True, help="Process run identifier."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/local.yml",
        help="Path to the YAML configuration file to load.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to scrape per brand/model combination.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Maximum number of parallel workers",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    args = parser.parse_args()
    logger = get_logger(__name__, args.log_level)

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()

    # Get inputs
    input_path = Path(config_manager.brands_and_models_path) / f"{args.run_id}.parquet"
    brands_data = file_service.read_parquet(input_path)

    for bd in brands_data.to_dict(orient="records"):
        # Create context for each batch
        context = StepContext(
            run_id=args.run_id,
            config_manager=config_manager,
            file_service=file_service,
            scraper_class=BrandListingsScraper,
            params={"brand_id": bd["brand_id"], "max_pages": args.max_pages, "log_level": args.log_level},
        )
        try:
            output = process_batch(context)
            logger.info(f"Run ID: {args.run_id}")
            logger.info(f"Batch ID: {bd['brand_id']}")
            logger.info(f"Number of inputs: {output.num_inputs}")
            logger.info(f"Successfully scraped {output.num_outputs} listings")
            logger.info(f"Output location: {output.output_dir}")
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    #
    # # Setup parallel processing
    # with multiprocessing.Pool(args.max_workers) as pool:
    #     jobs = []
    #     for bd in brands_data.to_dict(orient="records"):
    #         # Create context for each batch
    #         context = StepContext(
    #             run_id=args.run_id,
    #             config_manager=config_manager,
    #             file_service=file_service,
    #             scraper_class=BrandListingsScraper,
    #             params={"brand_id": bd["brand_id"], "max_pages": args.max_pages, "log_level": args.log_level},
    #         )
    #         jobs.append(pool.apply_async(process_batch, (context,)))
    #
    #     # Process results and collect statistics
    #     total_inputs = 0
    #     total_outputs = 0
    #     for job in jobs:
    #         try:
    #             output = job.get()
    #             total_inputs += output.num_inputs
    #             total_outputs += output.num_outputs
    #         except Exception as e:
    #             logger.error(f"Batch processing error: {e}")
    #
    #     # Print summary
    #     logger.info("\nProcessing completed!")
    #     logger.info(f"Run ID: {args.run_id}")
    #     logger.info(f"Number of inputs: {total_inputs}")
    #     logger.info(f"Successfully scraped {total_outputs} listings")
    #     logger.info(f"Output location: {config_manager.listings_path}/{run_id}")


if __name__ == "__main__":
    main()
