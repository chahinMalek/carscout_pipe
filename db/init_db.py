#!/usr/bin/env python3
import sqlite3
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_database(db_path: str) -> None:

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        logger.warning(f"Removing existing database at {db_path}")
        db_path.unlink()
    
    logger.info(f"Creating new database at {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        
        logger.info("Creating brands table...")
        cursor.execute('''
        CREATE TABLE brands (
            brand_id INTEGER PRIMARY KEY,
            brand_name TEXT NOT NULL,
            brand_slug TEXT NOT NULL
        )
        ''')
        
        logger.info("Creating vehicles table...")
        cursor.execute('''
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            title TEXT,
            price REAL,
            location TEXT,
            state TEXT,
            brand TEXT,
            model TEXT,
            fuel_type TEXT,
            build_year TEXT,
            mileage INTEGER,
            engine_volume REAL,
            engine_power REAL,
            num_doors TEXT,
            transmission TEXT,
            image_url TEXT,
            horsepower REAL,
            weight_kg REAL,
            vehicle_type TEXT,
            climate TEXT,
            audio TEXT,
            parking_sensors TEXT,
            parking_camera TEXT,
            drivetrain TEXT,
            year_first_registered TEXT,
            registered_until TEXT,
            color TEXT,
            gears TEXT,
            tyres TEXT,
            emission TEXT,
            interior TEXT,
            curtains TEXT,
            lights TEXT,
            number_of_seats TEXT,
            rim_size TEXT,
            warranty TEXT,
            security TEXT,
            previous_owners TEXT,
            published_at TEXT,
            registered NUMERIC,
            metallic NUMERIC,
            alloy_wheels NUMERIC,
            digital_air_conditioning NUMERIC,
            steering_wheel_controls NUMERIC,
            navigation NUMERIC,
            touch_screen NUMERIC,
            heads_up_display NUMERIC,
            usb_port NUMERIC,
            cruise_control NUMERIC,
            bluetooth NUMERIC,
            car_play NUMERIC,
            rain_sensor NUMERIC,
            park_assist NUMERIC,
            automatic_light_sensor NUMERIC,
            blind_spot_sensor NUMERIC,
            start_stop_system NUMERIC,
            hill_assist NUMERIC,
            seat_memory NUMERIC,
            seat_massage NUMERIC,
            seat_heating NUMERIC,
            seat_cooling NUMERIC,
            electric_windows NUMERIC,
            electric_seat_adjustment NUMERIC,
            armrest NUMERIC,
            panoramic_roof NUMERIC,
            sunroof NUMERIC,
            fog_lights NUMERIC,
            electric_mirrors NUMERIC,
            alarm NUMERIC,
            central_lock NUMERIC,
            remote_unlock NUMERIC,
            airbag NUMERIC,
            abs NUMERIC,
            electronic_stability NUMERIC,
            dpf_fap_filter NUMERIC,
            power_steering NUMERIC,
            turbo NUMERIC,
            isofix NUMERIC,
            tow_hook NUMERIC,
            customs_cleared NUMERIC,
            foreign_license_plates NUMERIC,
            on_lease NUMERIC,
            service_history NUMERIC,
            damaged NUMERIC,
            disabled_accessible NUMERIC,
            oldtimer NUMERIC,
            url TEXT NOT NULL,
            scraped_at TEXT,
            run_id TEXT NOT NULL,
            active NUMERIC NOT NULL,
            sold NUMERIC
        )
        ''')
        
        logger.info("Creating indexes...")
        cursor.execute('CREATE INDEX idx_vehicles_url ON vehicles(url)')
        cursor.execute('CREATE INDEX idx_vehicles_run_id ON vehicles(run_id)')
        cursor.execute('CREATE INDEX idx_vehicles_brand_model ON vehicles(brand, model)')
        cursor.execute('CREATE INDEX idx_vehicles_brand_model_year ON vehicles(brand, model, build_year)')

        logger.info("Inserting brands data...")
        cursor.executemany(
            'INSERT INTO brands (brand_id, brand_name, brand_slug) VALUES (?, ?, ?)',
            [
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
        )
        conn.commit()
        logger.info("Database initialization completed successfully")

        # todo: implement more checks if needed
        cursor.execute('SELECT COUNT(*) FROM brands')
        brands_count = cursor.fetchone()[0]
        logger.info(f"Verified {brands_count} brands in database")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.close()
        raise
    
    finally:
        conn.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Initialize the CarScout database")
    parser.add_argument(
        "--db-path",
        default="./data/carscout.db",
        help="Path where the database should be created"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Force database creation even if it already exists"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if Path(args.db_path).exists() and not args.overwrite:
        logger.error(
            f"Database already exists at {args.db_path}. "
            "Use --overwrite to overwrite it."
        )
        exit(1)

    try:
        init_database(args.db_path)
        exit(0)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        exit(1)
