from pathlib import Path

import pandas as pd

from src.pipeline.output import PipelineOutput
from src.pipeline.steps.base import PipelineStep, StepContext


class ScrapeBrandListingsStep(PipelineStep):
    def execute(self, context: StepContext) -> PipelineOutput:
        """Execute the listings scraping step for a single batch."""
        # Extract parameters
        brand_id = context.params["brand_id"]
        max_pages = context.params.get("max_pages", 5)
        log_level = context.params.get("log_level", "INFO")

        # Setup paths
        output_dir = Path(context.config_manager.listings_path) / context.run_id
        output_path = output_dir / f"{brand_id}.parquet"

        # Create output directory
        context.file_service.make_directory(output_dir, parents=True)

        # Initialize scraper
        kwargs = {"max_pages": max_pages, "log_level": log_level}
        scraper = context.scraper_class(
            context.config_manager, context.file_service, **kwargs
        )

        # Scrape listings
        successful_listings = scraper.scrape(brand_id)

        # Save successful results
        if successful_listings:
            listings_df = pd.DataFrame(successful_listings)
            context.file_service.write_parquet(listings_df, output_path, index=False)

        return PipelineOutput(
            step_name="scrape_listings",
            output_dir=output_dir,
            num_inputs=1,
            num_outputs=len(successful_listings),
            metadata={
                "brand_id": brand_id,
                "max_pages": max_pages,
                "output_path": str(output_path),
            },
        )
