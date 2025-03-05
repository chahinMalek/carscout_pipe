import argparse
import multiprocessing
import uuid
from pathlib import Path

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.vehicles import ScrapeVehiclesStep
from src.scrapers.vehicles import VehicleScraper
from src.utils.logging import get_logger


def process_batch(context: StepContext) -> None:
    """Process a single batch with proper error handling."""
    step = ScrapeVehiclesStep()
    return step.execute(context)


def main():
    parser = argparse.ArgumentParser(
        description="Scrapes vehicle information from listings.",
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

    # Get input batches
    input_dir = Path(config_manager.listings_path) / args.run_id
    batch_files = file_service.list_files(input_dir, pattern="*.parquet")
    if not batch_files:
        raise ValueError(f"No batch files found in {input_dir}")

    # Handle run id
    run_id = args.run_id or str(uuid.uuid4())

    # Setup parallel processing
    with multiprocessing.Pool(args.max_workers) as pool:
        jobs = []
        for batch_file in batch_files:
            # Create context for each batch
            context = StepContext(
                run_id=run_id,
                config_manager=config_manager,
                file_service=file_service,
                scraper_class=VehicleScraper,
                params={"batch_id": batch_file.stem, "log_level": args.log_level},
            )
            jobs.append(pool.apply_async(process_batch, (context,)))

        # Process results and handle errors
        total_inputs = 0
        total_outputs = 0

        for job in jobs:
            try:
                output = job.get()
                total_inputs += output.num_inputs
                total_outputs += output.num_outputs
            except Exception as e:
                logger.error(f"Batch processing error: {e}")

        # Print summary
        logger.info("\nProcessing completed!")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Number of batches: {len(batch_files)}")
        logger.info(f"Number of input listings: {total_inputs}")
        logger.info(f"Successfully scraped {total_outputs} vehicles")
        logger.info(f"Success rate: {total_outputs / total_inputs * 100:.2f}%")
        logger.info(f"Output directory: {config_manager.vehicles_path}/{run_id}")


if __name__ == "__main__":
    main()
