import argparse
import multiprocessing
import uuid
from pathlib import Path
import sys
from typing import List, Dict, Any
from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.brands_models import ScrapeBrandsAndModelsStep
from src.pipeline.steps.listings import ScrapeListingsStep
from src.pipeline.steps.vehicles import ScrapeVehiclesStep
from src.pipeline.steps.ingest_vehicles import IngestVehiclesStep
from src.pipeline.output import PipelineOutput

def run_parallel_step(step_class, batch_files: List[Path], context_params: Dict[str, Any], 
                     max_workers: int) -> Dict[str, int]:
    """Run a pipeline step in parallel across multiple batches."""
    
    with multiprocessing.Pool(max_workers) as pool:
        jobs = []
        for batch_file in batch_files:
            # Create context for each batch
            context = StepContext(
                run_id=context_params['run_id'],
                config_manager=context_params['config_manager'],
                file_service=context_params['file_service'],
                params={
                    "batch_id": batch_file.stem,
                    **context_params.get('step_params', {})
                }
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
            'processed': total_processed,
            'successful': total_successful,
        }

def main():
    parser = argparse.ArgumentParser(description='Run the complete scraping pipeline')
    parser.add_argument('--brands-file', required=True, help='Path to brands input file')
    parser.add_argument('--config', default='configs/local.yml', help='Path to config file')
    parser.add_argument('--max-workers', type=int, default=multiprocessing.cpu_count(),
                       help='Maximum number of parallel workers')
    parser.add_argument('--max-pages', type=int, default=20,
                       help='Maximum pages to scrape per brand/model combination')
    parser.add_argument('--chunk-size', type=int, default=10,
                       help='Size of chunks for brands and models')
    args = parser.parse_args()

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()
    
    # Generate run ID
    run_id = str(uuid.uuid4())
    print(f"Starting pipeline with run_id: {run_id}")
    try:
        # Step 1: Scrape brands and models
        print(f"\nExecuting Scraping brands and models step...")
        context = StepContext(
            run_id=run_id,
            config_manager=config_manager,
            file_service=file_service,
            params={
                "brands_file": args.brands_file,
                "chunk_size": args.chunk_size
            }
        )
        brands_output = ScrapeBrandsAndModelsStep().execute(context)
        print(f"\n--------------------------------")
        print(f"Scraping brands and models step completed:")
        print(f"Processed {brands_output.num_inputs} brands")
        print(f"Generated {brands_output.num_outputs} brand/model combinations")
        print(f"--------------------------------")
        
        # Common context parameters for parallel steps
        context_params = {
            'run_id': run_id,
            'config_manager': config_manager,
            'file_service': file_service
        }
        
        # Step 2: Scrape listings (parallel)
        listings_input_dir = Path(config_manager.brands_and_models_path) / run_id
        listings_batches = file_service.list_files(listings_input_dir, pattern="*.parquet")
        context_params['step_params'] = {'max_pages': args.max_pages}
        
        print(f"\nExecuting Scraping listings step...")
        listings_stats = run_parallel_step(
            ScrapeListingsStep,
            listings_batches,
            context_params,
            args.max_workers,
        )
        print(f"\n--------------------------------")
        print(f"Scraping listings step completed:")
        print(f"Processed {listings_stats['processed']} listings")
        print(f"Successfully processed {listings_stats['successful']} listings")
        print(f"--------------------------------")
        
        # Step 3: Scrape vehicles (parallel)
        print(f"\nExecuting Scraping vehicles step...")
        vehicles_input_dir = Path(config_manager.listings_path) / run_id
        vehicles_batches = file_service.list_files(vehicles_input_dir, pattern="*.parquet")
        context_params['step_params'] = {}
        
        vehicles_stats = run_parallel_step(
            ScrapeVehiclesStep,
            vehicles_batches,
            context_params,
            args.max_workers,
        )
        print(f"\n--------------------------------")
        print(f"Scraping vehicles step completed:")
        print(f"Processed {vehicles_stats['processed']} vehicles")
        print(f"Successfully processed {vehicles_stats['successful']} vehicles")
        print(f"--------------------------------")
        
        # Step 4: Ingest vehicles
        print(f"\nExecuting Vehicles ingestion step...")
        ingest_context = StepContext(
            run_id=run_id,
            config_manager=config_manager,
            file_service=file_service,
            params={}
        )
        ingest_output = IngestVehiclesStep().execute(ingest_context)
        print(f"\n--------------------------------")
        print(f"Vehicles ingestion step completed:")
        print(f"Processed {ingest_output.num_inputs} vehicles")
        print(f"Successfully ingested {ingest_output.num_outputs} vehicles")
        print(f"--------------------------------")
        
        # Print final summary
        print(f"\n--------------------------------")
        print("Pipeline completed successfully!")
        print(f"Run ID: {run_id}")
        print("\nFinal Statistics:")
        print(f"Brands/Models: {brands_output.num_outputs} combinations generated")
        print(f"Listings: {listings_stats['successful']} successfully scraped")
        scraped_vehicles_pct = vehicles_stats['successful'] / vehicles_stats['processed'] * 100
        print(f"Vehicles: {vehicles_stats['successful']}/{vehicles_stats['processed']} successfully scraped ({scraped_vehicles_pct:.2f}%)")
        ingested_vehicles_pct = ingest_output.num_outputs / ingest_output.num_inputs * 100
        print(f"Database: {ingest_output.num_outputs}/{ingest_output.num_inputs} vehicles ingested ({ingested_vehicles_pct:.2f}%)")
        print(f"--------------------------------")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
