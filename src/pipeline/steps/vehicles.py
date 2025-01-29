from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

from src.pipeline.steps.base import PipelineStep, StepContext
from src.pipeline.output import PipelineOutput
from src.scrapers.vehicles import VehicleScraper

class ScrapeVehiclesStep(PipelineStep):
    def execute(self, context: StepContext) -> PipelineOutput:
        """Execute the vehicles scraping step for a single batch."""
        # Setup paths
        batch_id = context.params['batch_id']
        input_path = Path(context.config_manager.listings_path) / context.run_id / f"{batch_id}.parquet"
        output_dir = Path(context.config_manager.vehicles_path) / context.run_id
        output_path = output_dir / f"{batch_id}.parquet"
        
        # Validate input file
        if not context.file_service.file_exists(input_path):
            raise ValueError(f"Input file not found at {input_path}")
        
        # Create output directory
        context.file_service.make_directory(output_dir, parents=True)
        
        # Initialize scraper
        scraper = context.scraper_class(context.config_manager, context.file_service)
        
        # Read and prepare input batch
        listings = context.file_service.read_parquet(input_path)
        listings = listings.drop_duplicates(ignore_index=True)
        listings = listings.to_dict("records")

        # Scrape vehicles
        successful_vehicles = scraper.scrape(listings)
        
        # Save successful results
        if successful_vehicles:
            vehicles_df = pd.DataFrame(successful_vehicles)
            vehicles_df = vehicles_df.astype(str)
            context.file_service.write_parquet(vehicles_df, output_path, index=False)
        
        return PipelineOutput(
            step_name="scrape_vehicles",
            output_dir=output_dir,
            num_inputs=len(listings),
            num_outputs=len(successful_vehicles),
            metadata={
                'batch_id': batch_id,
                'input_path': str(input_path),
                'output_path': str(output_path)
            }
        ) 