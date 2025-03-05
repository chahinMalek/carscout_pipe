import argparse
import multiprocessing
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.output import PipelineOutput
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.brands_models import ScrapeBrandsAndModelsStep
from src.pipeline.steps.ingest_vehicles import IngestVehiclesStep
from src.pipeline.steps.listings import ScrapeListingsStep
from src.pipeline.steps.vehicles import ScrapeVehiclesStep
from src.scrapers import BrandsAndModelsScraper, ListingsScraper, VehicleScraper
from src.utils.logging import get_logger


def run_parallel_step(
    step_class,
    batch_files: List[Path],
    context_params: Dict[str, Any],
    max_workers: int,
) -> Dict[str, int]:
    """Run a pipeline step in parallel across multiple batches."""

    with multiprocessing.Pool(max_workers) as pool:
        jobs = []
        for batch_file in batch_files:
            # Create context for each batch
            context = StepContext(
                run_id=context_params["run_id"],
                config_manager=context_params["config_manager"],
                file_service=context_params["file_service"],
                scraper_class=context_params.get("scraper_class"),
                params={
                    "batch_id": batch_file.stem,
                    "log_level": context_params["log_level"],
                    **context_params.get("step_params", {}),
                },
            )
            jobs.append(pool.apply_async(step_class().execute, (context,)))

        # Process results and collect statistics
        total_processed = 0
        total_successful = 0

        for job in jobs:
            try:
                output: PipelineOutput = job.get()
                total_processed += output.num_inputs
                total_successful += output.num_outputs
            except Exception as e:
                print(f"Batch processing error: {e}")

        return {
            "processed": total_processed,
            "successful": total_successful,
        }


def main():
    parser = argparse.ArgumentParser(description="Run the complete scraping pipeline")
    parser.add_argument(
        "--brands-file", required=True, help="Path to brands input file"
    )
    parser.add_argument(
        "--config", default="configs/local.yml", help="Path to config file"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Maximum number of parallel workers",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum pages to scrape per brand/model combination",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10,
        help="Size of chunks for brands and models",
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

    # Generate run ID
    run_id = str(uuid.uuid4())
    logger.info(f"Starting pipeline with run_id: {run_id}")
    try:
        # Step 1: Scrape brands and models
        logger.info("\nExecuting Scraping brands and models step ...")
        brands_output = ScrapeBrandsAndModelsStep().execute(
            StepContext(
                run_id=run_id,
                config_manager=config_manager,
                file_service=file_service,
                scraper_class=BrandsAndModelsScraper,
                params={"brands_file": args.brands_file, "chunk_size": args.chunk_size, "log_level": args.log_level},
            )
        )
        logger.info("\n--------------------------------")
        logger.info("Scraping brands and models step completed:")
        logger.info(f"Processed {brands_output.num_inputs} brands")
        logger.info(f"Generated {brands_output.num_outputs} brand/model combinations")
        logger.info("--------------------------------")

        # Common context parameters for parallel steps
        context_params = {
            "run_id": run_id,
            "config_manager": config_manager,
            "file_service": file_service,
            "log_level": args.log_level,
        }

        # Step 2: Scrape listings (parallel)
        listings_input_dir = Path(config_manager.brands_and_models_path) / run_id
        listings_batches = file_service.list_files(
            listings_input_dir, pattern="*.parquet"
        )
        context_params["step_params"] = {"max_pages": args.max_pages}
        context_params["scraper_class"] = ListingsScraper

        logger.info("\nExecuting Scraping listings step ...")
        listings_stats = run_parallel_step(
            ScrapeListingsStep,
            listings_batches,
            context_params,
            args.max_workers,
        )
        logger.info("\n--------------------------------")
        logger.info("Scraping listings step completed:")
        logger.info(f"Processed {listings_stats['processed']} listings")
        logger.info(f"Successfully processed {listings_stats['successful']} listings")
        logger.info("--------------------------------")

        # Step 3: Scrape vehicles (parallel)
        logger.info("\nExecuting Scraping vehicles step ...")
        vehicles_input_dir = Path(config_manager.listings_path) / run_id
        vehicles_batches = file_service.list_files(
            vehicles_input_dir, pattern="*.parquet"
        )
        context_params["step_params"] = {}
        context_params["scraper_class"] = VehicleScraper

        vehicles_stats = run_parallel_step(
            ScrapeVehiclesStep,
            vehicles_batches,
            context_params,
            args.max_workers,
        )
        logger.info("\n--------------------------------")
        logger.info("Scraping vehicles step completed:")
        logger.info(f"Processed {vehicles_stats['processed']} vehicles")
        logger.info(f"Successfully processed {vehicles_stats['successful']} vehicles")
        logger.info("--------------------------------")

        # Step 4: Ingest vehicles
        logger.info("\nExecuting Vehicles ingestion step ...")
        ingest_output = IngestVehiclesStep().execute(
            StepContext(
                run_id=run_id,
                config_manager=config_manager,
                file_service=file_service,
                params={},
            )
        )
        logger.info("\n--------------------------------")
        logger.info("Vehicles ingestion step completed:")
        logger.info(f"Processed {ingest_output.num_inputs} vehicles")
        logger.info(f"Successfully ingested {ingest_output.num_outputs} vehicles")
        logger.info("--------------------------------")

        # Print final summary
        logger.info("\n--------------------------------")
        logger.info("Pipeline completed successfully!")
        logger.info(f"Run ID: {run_id}")
        logger.info("\nFinal Statistics:")
        logger.info(f"Brands/Models: {brands_output.num_outputs} combinations generated")
        logger.info(f"Listings: {listings_stats['successful']} successfully scraped")
        scraped_vehicles_pct = (
            vehicles_stats["successful"] / vehicles_stats["processed"] * 100
        )
        logger.info(
            f"Vehicles: {vehicles_stats['successful']}/{vehicles_stats['processed']} successfully scraped ({scraped_vehicles_pct:.2f}%)"
        )
        ingested_vehicles_pct = (
            ingest_output.num_outputs / ingest_output.num_inputs * 100
        )
        logger.info(
            f"Database: {ingest_output.num_outputs}/{ingest_output.num_inputs} vehicles ingested ({ingested_vehicles_pct:.2f}%)"
        )
        logger.info("--------------------------------")

    except Exception as e:
        logger.error(f"\nPipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
