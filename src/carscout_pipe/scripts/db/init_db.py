#!/usr/bin/env python3
"""
Database initialization script for CarScout pipeline.

This script initializes the database schema and can be used to:
- Create all tables
- Drop and recreate tables (reset)
"""

import argparse

from src.carscout_pipe.infra.db.service import db_service
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    db_service.initialize_database()
    logger.info("Database initialization completed.")


def reset_database():
    """Drop and recreate all database tables."""
    logger.info("Resetting database (dropping all tables)...")
    db_service.db_manager.drop_tables()
    logger.info("Tables dropped. Recreating...")
    db_service.initialize_database()
    logger.info("Database reset completed.")


def main():
    parser = argparse.ArgumentParser(description="Initialize CarScout database")
    parser.add_argument(
        "--reset", action="store_true", help="Drop and recreate all tables"
    )

    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        init_database()

    logger.info("Database setup completed successfully.")


if __name__ == "__main__":
    main()
