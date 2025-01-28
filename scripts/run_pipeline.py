import argparse
import subprocess
import uuid
from pathlib import Path
import multiprocessing
from typing import List
import sys
import os
import pandas as pd

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.config import Config, ConfigManager
from src.io.file_service import FileService, LocalFileService


def run_command(cmd: List[str], description: str) -> None:
    """Run a command and handle its output/errors."""
    print(f"\nExecuting {description}...")
    try:        
        # Set PYTHONPATH to include the project root
        env = os.environ.copy()
        project_root = str(Path(__file__).parent.parent)
        env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
        
        # Run as subprocess with real-time output
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}:", file=sys.stderr)
        raise

def get_batch_files(directory: str) -> List[Path]:
    """Get all parquet files in the directory."""
    return sorted(Path(directory).glob("*.parquet"))

def process_batch(cmd: List[str], description: str) -> None:
    """Process a single batch with proper error handling."""
    try:
        run_command(cmd, description)
    except subprocess.CalledProcessError as e:
        print(f"Failed to process batch: {e}", file=sys.stderr)
        raise

def run_parallel_processing(base_cmd: List[str], input_dir: Path, 
                          max_workers: int, description: str) -> None:
    """Run multiple batch processes in parallel with worker limit."""
    batch_files = get_batch_files(input_dir)
    if not batch_files:
        raise ValueError(f"No batch files found in {input_dir}")

    with multiprocessing.Pool(max_workers) as pool:
        jobs = []
        for batch_file in batch_files:
            batch_id = batch_file.stem
            cmd = base_cmd + ["--batch-id", batch_id]
            jobs.append(pool.apply_async(process_batch, (cmd, f"{description} batch {batch_id}")))
        
        # Wait for all jobs to complete and check for errors
        for job in jobs:
            try:
                job.get()  # This will raise any exceptions that occurred
            except Exception as e:
                print(f"A batch failed: {e}", file=sys.stderr)
                pool.terminate()
                raise

def cleanup_and_summarize(run_id: str, config_manager: ConfigManager, file_service: FileService) -> None:
    """Merge listings and vehicles data, generate statistics, and cleanup."""
    print("\nGenerating summary statistics...")
    
    # Setup paths
    base_path = Path(config_manager.base_path)
    brands_and_models_path = Path(config_manager.brands_and_models_path) / run_id
    listings_path = Path(config_manager.listings_path) / run_id
    vehicles_path = Path(config_manager.vehicles_path) / run_id
    outputs_path = base_path / "outputs"
    
    outputs_path.mkdir(exist_ok=True)
    
    # Read and merge data
    listings = file_service.read_parquet(listings_path)
    vehicles = file_service.read_parquet(vehicles_path)
    merged = pd.merge(listings[["url"]], vehicles, on='url', how='left')
    
    # Calculate statistics
    total_listings = merged.shape[0]
    successful_scrapes = len(merged[~merged['title'].isna()])
    success_rate = (successful_scrapes / total_listings) * 100
    
    # Print summary
    print(f"\nScraping Summary:")
    print(f"Total listings found: {total_listings}")
    print(f"Successfully scraped vehicles: {successful_scrapes}")
    print(f"Success rate: {success_rate:.2f}%")

    # Save merged results
    output_file = outputs_path / f"{run_id}.parquet"
    file_service.write_parquet(merged, output_file)
    print(f"\nMerged data saved to: {output_file}")
    
    # Cleanup temporary directories
    print("\nCleaning up temporary directories...")
    print(f"Removing {brands_and_models_path} ...")
    file_service.remove_directory(brands_and_models_path)
    print(f"Removing {listings_path} ...")
    file_service.remove_directory(listings_path)
    print(f"Removing {vehicles_path} ...")
    file_service.remove_directory(vehicles_path)
    print("Cleanup completed.")

def main():
    parser = argparse.ArgumentParser(description='Run the complete scraping pipeline')
    parser.add_argument('--brands-file', required=True, help='Path to brands input file')
    parser.add_argument('--config', default='configs/local.yml', help='Path to config file')
    parser.add_argument('--max-workers', type=int, default=multiprocessing.cpu_count(),
                       help='Maximum number of parallel workers')
    parser.add_argument('--max-pages', type=int, default=20,
                       help='Maximum pages to scrape per brand/model combination')
    parser.add_argument('--chunk-size', type=int, default=100,
                       help='Size of chunks for brands and models')
    args = parser.parse_args()

    # Instantiate services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()

    # Generate a unique run ID for this pipeline execution
    run_id = str(uuid.uuid4())
    print(f"Starting pipeline with run_id: {run_id}")

    try:
        # Step 1: Scrape brands and models
        cmd = [
            "python", "scripts/scrape_brands_and_models.py",
            "--run-id", run_id,
            "--brands", args.brands_file,
            "--config", args.config,
            "--chunk-size", str(args.chunk_size)
        ]
        run_command(cmd, "Scraping brands and models")

        # Step 2: Scrape listings (parallel processing)
        base_cmd = [
            "python", "scripts/scrape_listings.py",
            "--run-id", run_id,
            "--config", args.config,
            "--max-pages", str(args.max_pages)
        ]
        input_dir = str(Path(config_manager.brands_and_models_path) / run_id)
        run_parallel_processing(base_cmd, input_dir, args.max_workers, "Scraping listings")

        # Step 3: Scrape vehicles (parallel processing)
        base_cmd = [
            "python", "scripts/scrape_vehicles.py",
            "--run-id", run_id,
            "--config", args.config
        ]
        input_dir = str(Path(config_manager.listings_path) / run_id)
        run_parallel_processing(base_cmd, input_dir, args.max_workers, "Scraping vehicles")

        # Step 4: Ingest data into database
        cmd = [
            "python", "scripts/ingest_into_db.py",
            "--run-id", run_id,
        ]
        run_command(cmd, "Ingesting data into database")

        # Step 5: Cleanup and summarize results
        cleanup_and_summarize(run_id, config_manager, file_service)

        print("\nPipeline completed successfully!")
        print(f"Run ID: {run_id}")

        

    except Exception as e:
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 