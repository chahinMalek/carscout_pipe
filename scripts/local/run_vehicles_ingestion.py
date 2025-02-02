import argparse

from src.config import Config, ConfigManager
from src.io.file_service import LocalFileService
from src.pipeline.steps.base import StepContext
from src.pipeline.steps.ingest_vehicles import IngestVehiclesStep


def main():
    parser = argparse.ArgumentParser(
        description="Ingest scraped vehicles into the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Unique identifier for this scraping run. Required.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/local.yml",
        help="Path to the YAML configuration file to load.",
    )
    args = parser.parse_args()

    # Initialize services
    config_manager = ConfigManager(Config.load(args.config))
    file_service = LocalFileService()

    # Create step context
    context = StepContext(
        run_id=args.run_id,
        config_manager=config_manager,
        file_service=file_service,
        params={},
    )

    # Execute step
    step = IngestVehiclesStep()
    output = step.execute(context)

    print("\nStep completed successfully!")
    print(f"Run ID: {context.run_id}")
    print(f"Number of inputs: {output.num_inputs}")
    print(f"Ingested {output.num_outputs} records")
    print(f"Output directory: {output.output_dir}")


if __name__ == "__main__":
    main()
