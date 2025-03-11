#!/usr/bin/env python3
import sqlite3
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Hardcoded brands data
BRANDS_DATA = [
    (85, "Toyota", "toyota"),
    (7, "Audi", "audi"),
    (61, "Nissan", "nissan"),
    (56, "Mercedes-Benz", "mercedes-benz"),
    (65, "Peugeot", "peugeot"),
    (59, "Mitsubishi", "mitsubishi"),
    (89, "Volkswagen", "volkswagen"),
    (90, "Volvo", "volvo"),
    (71, "Renault", "renault"),
    (29, "Fiat", "fiat"),
    (35, "Hyundai", "hyundai"),
    (3, "Alfa Romeo", "alfa-romeo"),
    (11, "BMW", "bmw"),
    (30, "Ford", "ford"),
    (41, "Kia", "kia"),
    (64, "Opel", "opel"),
    (82, "Suzuki", "suzuki"),
    (20, "Citroen", "citroen"),
    (77, "Škoda", "skoda"),
    (40, "Jeep", "jeep"),
    (55, "Mazda", "mazda"),
    (106, "Cupra", "cupra"),
    (76, "Seat", "seat"),
]

def init_database(db_path: str) -> None:
    """
    Initialize the database with schema and brands data.
    
    Args:
        db_path: Path where the database should be created
    """
    # Convert to Path object for easier manipulation
    db_path = Path(db_path)
    
    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if it exists
    if db_path.exists():
        logger.warning(f"Removing existing database at {db_path}")
        db_path.unlink()
    
    # Create and initialize database
    logger.info(f"Creating new database at {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        
        # Create brands table
        logger.info("Creating brands table...")
        cursor.execute('''
        CREATE TABLE brands (
            brand_id INTEGER PRIMARY KEY,
            brand_name TEXT NOT NULL,
            brand_slug TEXT NOT NULL
        )
        ''')
        
        # Create vehicles table
        logger.info("Creating vehicles table...")
        cursor.execute('''
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            price REAL,
            currency TEXT,
            location TEXT,
            registration_year INTEGER,
            mileage INTEGER,
            fuel_type TEXT,
            engine_displacement INTEGER,
            transmission_type TEXT,
            body_type TEXT,
            color TEXT,
            condition TEXT,
            description TEXT,
            brand TEXT,
            model TEXT,
            scraped_at TEXT,
            run_id TEXT
        )
        ''')
        
        # Create indexes
        logger.info("Creating indexes...")
        cursor.execute('CREATE INDEX idx_vehicles_url ON vehicles(url)')
        cursor.execute('CREATE INDEX idx_vehicles_brand ON vehicles(brand)')
        cursor.execute('CREATE INDEX idx_vehicles_run_id ON vehicles(run_id)')
        
        # Insert brands data
        logger.info("Inserting brands data...")
        cursor.executemany(
            'INSERT INTO brands (brand_id, brand_name, brand_slug) VALUES (?, ?, ?)',
            BRANDS_DATA
        )
        
        # Commit changes
        conn.commit()
        logger.info("Database initialization completed successfully")
        
        # Verify brands data
        cursor.execute('SELECT COUNT(*) FROM brands')
        brands_count = cursor.fetchone()[0]
        logger.info(f"Verified {brands_count} brands in database")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        # Remove database file if initialization failed
        conn.close()
        db_path.unlink()
        raise
    
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Initialize the CarScout database")
    parser.add_argument(
        "--db-path",
        default="carscout.db",
        help="Path where the database should be created"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force database creation even if it already exists"
    )
    
    args = parser.parse_args()
    
    # Check if database already exists
    if Path(args.db_path).exists() and not args.force:
        logger.error(
            f"Database already exists at {args.db_path}. "
            "Use --force to overwrite it."
        )
        return 1
    
    try:
        init_database(args.db_path)
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 