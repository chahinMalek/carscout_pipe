import argparse
import uuid

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.brands_models import ScrapeBrandsAndModelsStep

def main():
    parser = argparse.ArgumentParser(
        description='Scrapes car brands and models data from olx.ba.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--run-id', type=str,
                        help='Unique identifier for this scraping run. If not provided, a random UUID will be generated.')
    parser.add_argument('--brands', type=str, required=True,
                        help='Path to CSV file containing list of car brands to scrape.')
    parser.add_argument('--config', type=str, default='configs/local.yml',
                        help='Path to the YAML configuration file to load.')
    parser.add_argument('--chunk-size', type=int, default=10,
                        help='Number of items to store in each output chunk.')
    args = parser.parse_args()

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()
    
    # Create step context
    context = StepContext(
        run_id=args.run_id or str(uuid.uuid4()),
        config_manager=config_manager,
        file_service=file_service,
        params={
            "brands_file": args.brands,
            "chunk_size": args.chunk_size
        }
    )
    
    # Execute step
    step = ScrapeBrandsAndModelsStep()
    output = step.execute(context)

    print("\nStep completed successfully!")
    print(f"Run ID: {context.run_id}")
    print(f"Number of inputs: {output.num_inputs}")
    print(f"Collected {output.num_outputs} records")
    print(f"Output directory: {output.output_dir}")

if __name__ == "__main__":
    main() 