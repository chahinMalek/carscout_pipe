from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

from src.pipeline.steps.base import PipelineStep, StepContext
from src.pipeline.output import PipelineOutput


class IngestVehiclesStep(PipelineStep):
    def execute(self, context: StepContext) -> PipelineOutput:
        """Execute the ingestion step."""

        # DB connection
        db_params = context.config_manager.db_connection_params
        client = MongoClient(db_params["host"])
        db_name = db_params["database"]
        collection_name = context.config_manager.db_collections["vehicles"]
        collection = client[db_name][collection_name]

        # Read input data
        input_path = Path(context.config_manager.vehicles_path) / context.run_id
        if not context.file_service.directory_exists(input_path):
            raise ValueError(f"Input files not found at {input_path}")

        vehicles = context.file_service.read_parquet(input_path)
        vehicles = vehicles.to_dict("records")

        # Retrieve existing URLs from the database
        existing_urls = set(collection.distinct("url"))
        print(f"Retrieved {len(existing_urls)} existing URLs from the database.")

        # Remove existing records from the database
        collection.delete_many({"url": {"$in": existing_urls}})
        print(f"Deleted {len(existing_urls)} existing records from the database.")

        # Process each Parquet file
        total_inputs = 0
        total_ingested = 0
        for partfile in context.file_service.list_files(
            input_path, pattern="*.parquet"
        ):
            print(f"Processing file: {partfile}")

            # Read Parquet file into a DataFrame
            df = context.file_service.read_parquet(partfile)
            total_inputs += len(df)
            df["specs"] = df["specs"].apply(lambda s: eval(s))
            df["ingested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df = df.reset_index(drop=True)
            records = df.to_dict(orient="records")
            total_ingested += len(records)

            # Insert records into MongoDB collection
            if records:
                collection.insert_many(records)
                print(f"Inserted {len(records)} records from {partfile} into MongoDB.")

        return PipelineOutput(
            step_name="ingest_vehicles",
            output_dir=f"{db_name}.{collection_name}",
            num_inputs=total_inputs,
            num_outputs=total_ingested,
            metadata={"run_id": context.run_id},
        )
