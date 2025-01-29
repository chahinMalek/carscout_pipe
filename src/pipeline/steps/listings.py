from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

from src.pipeline.steps.base import PipelineStep, StepContext
from src.pipeline.output import PipelineOutput
from src.scrapers.listings import ListingsScraper


class ScrapeListingsStep(PipelineStep):
    def execute(self, context: StepContext) -> PipelineOutput:
        """Execute the listings scraping step for a single batch."""
        # Extract parameters
        batch_id = context.params['batch_id']
        max_pages = context.params.get('max_pages', 5)
        
        # Setup paths
        input_path = Path(context.config_manager.brands_and_models_path) / context.run_id / f"{batch_id}.parquet"
        output_dir = Path(context.config_manager.listings_path) / context.run_id
        output_path = output_dir / f"{batch_id}.parquet"
        
        # Validate input file
        if not context.file_service.file_exists(input_path):
            raise ValueError(f"Input file not found at {input_path}")
        
        # Create output directory
        context.file_service.make_directory(output_dir, parents=True)
        
        # Initialize scraper
        kwargs = {"max_pages": max_pages}
        scraper = context.scraper_class(context.config_manager, context.file_service, **kwargs)
        
        # Read input batch
        brands_and_models = context.file_service.read_parquet(input_path)
        brands_and_models = brands_and_models.to_dict("records")

        # Scrape listings
        successful_listings = scraper.scrape(brands_and_models)
        
        # Save successful results
        if successful_listings:
            listings_df = pd.DataFrame(successful_listings)
            context.file_service.write_parquet(listings_df, output_path, index=False)
        
        return PipelineOutput(
            step_name="scrape_listings",
            output_dir=output_dir,
            num_inputs=len(brands_and_models),
            num_outputs=len(successful_listings),
            metadata={
                'batch_id': batch_id,
                'max_pages': max_pages,
                'input_path': str(input_path),
                'output_path': str(output_path)
            }
        ) 