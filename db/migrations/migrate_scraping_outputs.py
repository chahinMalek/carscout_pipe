import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from carscout_pipe.data_models.vehicles.schema import Vehicle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_dataset(input_dir: str, run_id: str) -> pd.DataFrame:
    partfiles_dir = Path(input_dir).joinpath(run_id)
    if not partfiles_dir.exists():
        raise FileNotFoundError(f"Directory {partfiles_dir} does not exist.")

    chunks = []
    partfiles = list(partfiles_dir.glob("*.csv"))
    
    if not partfiles:
        raise ValueError(f"No partfiles found in {partfiles_dir}")

    for partfile in partfiles:
        try:
            df = pd.read_csv(partfile)
            if df.empty:
                logger.warning(f"Empty CSV file: {partfile}")
                continue
            chunks.append(df)
        except pd.errors.EmptyDataError:
            logger.warning(f"Failed to read empty partfile: {partfile}")
        except Exception as err:
            logger.error(f"Error reading {partfile}: {str(err)}")
            continue

    if not chunks:
        raise ValueError("No valid data found in any partfiles")

    dataset = pd.concat(chunks, ignore_index=True)
    return dataset


def insert_vehicles_batch(db: sqlite3.Connection, vehicles: list[Vehicle], batch_size: int = 1000) -> tuple[int, int]:
    cursor = db.cursor()
    failed_count = 0
    success_count = 0

    fields = [field for field in Vehicle.model_fields.keys()]
    placeholders = ','.join(['?' for _ in fields])
    query = f"INSERT INTO vehicles ({','.join(fields)}) VALUES ({placeholders})"
    
    try:
        db.execute("BEGIN TRANSACTION")
        
        for i in range(0, len(vehicles), batch_size):
            batch = vehicles[i:i + batch_size]
            values = [
                [getattr(vehicle, field) for field in fields]
                for vehicle in batch
            ]
            cursor.executemany(query, values)
            success_count += len(batch)
            
        db.commit()
        logger.info(f"Successfully inserted {success_count} vehicles")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during batch insert: {e}")
        raise
        
    return success_count, failed_count


if __name__ == "__main__":

    # run_id = "64fddb00-4834-4655-827b-1722a00bf908"
    run_id = "ae7deaf6-9d1d-4565-bb38-487b5f9cafd8"
    input_dir = "data/output/"
    db_path = "data/carscout.db"

    # step 1: build dataset
    dataset_path = Path(input_dir).joinpath(f"{run_id}.csv")
    if not dataset_path.exists():
        logger.info(f"Building dataset from partfiles for run {run_id}")
        try:
            dataset = build_dataset(input_dir, run_id)
        except FileNotFoundError as e:
            logger.error(f"Directory or file not found: {e}")
            exit(1)
        except ValueError as e:
            logger.error(str(e))
            exit(1)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            exit(1)
        dataset.to_csv(dataset_path, index=False)
        logger.info(f"Dataset saved to {dataset_path}")

    logger.info(f"Loading dataset from {dataset_path}")
    dataset = pd.read_csv(dataset_path)
    dataset["active"] = True
    dataset["sold"] = False

    # step 2: perform validation
    valid_vehicles = []
    validation_errors = 0
    logger.info("Validating vehicles...")

    for _, row in dataset.iterrows():
        try:
            vehicle = Vehicle.from_raw_dict(row.replace({np.nan: None}).to_dict())
            valid_vehicles.append(vehicle)
        except Exception as e:
            validation_errors += 1
            logger.warning(f"Validation error for row: {e}")
            continue

    logger.info(f"Validation complete. {len(valid_vehicles)} valid vehicles, {validation_errors} validation errors")

    # step 3: insert vehicles into database
    db = sqlite3.connect(db_path)

    if valid_vehicles:
        try:
            success_count, failed_count = insert_vehicles_batch(db, valid_vehicles)
            logger.info(f"Migration complete. Inserted {success_count} vehicles")
        except Exception as e:
            logger.error(f"Failed to insert vehicles: {e}")
            exit(1)
    else:
        logger.error("No valid vehicles to insert")
        exit(1)

    db.close()
