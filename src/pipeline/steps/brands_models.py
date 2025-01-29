from pathlib import Path

import pandas as pd

from src.pipeline.steps.base import PipelineStep, StepContext
from src.pipeline.output import PipelineOutput


class ScrapeBrandsAndModelsStep(PipelineStep):
    def execute(self, context: StepContext) -> PipelineOutput:
        """Execute the brands and models scraping step."""

        # Validate required parameters
        if 'brands_file' not in context.params:
            raise ValueError("brands_file parameter is required")
        
        # Extract parameters
        brands_path = Path(context.params['brands_file'])
        chunk_size = context.params.get('chunk_size', 10)
        
        # Validate inputs
        if not context.file_service.file_exists(brands_path):
            raise ValueError(f"Brands file not found at {brands_path}")

        # Initialize scraper
        scraper = context.scraper_class(context.config_manager, context.file_service)        
        
        # Setup output directory
        output_dir = Path(context.config_manager.brands_and_models_path) / context.run_id
        context.file_service.make_directory(output_dir, parents=True)
        
        # Execute scraping
        brands = context.file_service.read_lines(brands_path)
        brands_and_models_data = scraper.scrape(brands)
        
        # Process and save results
        df = pd.DataFrame(brands_and_models_data)
        df = df.sample(frac=1, random_state=42, ignore_index=True)
        context.file_service.write_parquet_chunked(df, output_dir, chunk_size)

        return PipelineOutput(
            step_name="scrape_brands_models",
            output_dir=output_dir,
            num_inputs=len(brands),
            num_outputs=len(df),
            metadata={
                'chunk_size': chunk_size,
                'brands_file': str(brands_path),
                'run_id': context.run_id
            }
        )
