#!/usr/bin/env python3
"""
Database query utilities for CarScout pipeline.

This script provides utilities to query and analyze scraped data.
"""

import argparse
from datetime import datetime, timedelta

from src.carscout_pipe.infra.db.connection import db_manager
from src.carscout_pipe.infra.db.models import ListingModel
from src.carscout_pipe.infra.logging import get_logger

logger = get_logger(__name__)


def show_recent_listings(hours: int = 24):
    """Show recently scraped listings."""
    with db_manager.get_session() as session:
        cutoff_date = datetime.now() - timedelta(hours=hours)
        listings = session.query(ListingModel).filter(
            ListingModel.scraped_at >= cutoff_date
        ).order_by(ListingModel.scraped_at.desc()).limit(20).all()
        
        print(f"\nRecent listings (last {hours} hours, max 20):")
        print("-" * 120)
        print(f"{'Title':<50} {'Price':<15} {'Scraped At':<20} {'Run ID':<36}")
        print("-" * 120)
        
        for listing in listings:
            title = listing.title[:47] + "..." if len(listing.title) > 50 else listing.title
            scraped = listing.scraped_at.strftime("%Y-%m-%d %H:%M:%S")
            run_id = listing.run_id[:8] + "..." if listing.run_id and len(listing.run_id) > 8 else listing.run_id or "N/A"
            print(f"{title:<50} {listing.price or 'N/A':<15} {scraped:<20} {run_id:<36}")


def show_runs_summary():
    """Show summary of scraping runs."""
    with db_manager.get_session() as session:
        # Group listings by run_id and get counts
        from sqlalchemy import func
        results = session.query(
            ListingModel.run_id,
            func.count(ListingModel.id).label('listing_count'),
            func.min(ListingModel.scraped_at).label('started_at'),
            func.max(ListingModel.scraped_at).label('ended_at')
        ).filter(
            ListingModel.run_id.isnot(None)
        ).group_by(ListingModel.run_id).order_by(
            func.min(ListingModel.scraped_at).desc()
        ).limit(10).all()
        
        print("\nRecent scraping runs (last 10):")
        print("-" * 100)
        print(f"{'Run ID':<36} {'Listings':<10} {'Started':<20} {'Ended':<20}")
        print("-" * 100)
        
        for run_id, count, started, ended in results:
            started_str = started.strftime("%Y-%m-%d %H:%M:%S") if started else "N/A"
            ended_str = ended.strftime("%Y-%m-%d %H:%M:%S") if ended else "N/A"
            print(f"{run_id:<36} {count:<10} {started_str:<20} {ended_str:<20}")


def show_database_stats():
    """Show overall database statistics."""
    with db_manager.get_session() as session:
        total_listings = session.query(ListingModel).count()
        
        # Get latest scraping activity
        latest_listing = session.query(ListingModel).order_by(
            ListingModel.scraped_at.desc()
        ).first()
        
        # Get unique run count
        from sqlalchemy import func
        unique_runs = session.query(func.count(func.distinct(ListingModel.run_id))).scalar()
        
        print("\nDatabase Statistics:")
        print("-" * 30)
        print(f"Total Listings: {total_listings}")
        print(f"Unique Runs: {unique_runs}")
        
        if latest_listing:
            latest_date = latest_listing.scraped_at.strftime("%Y-%m-%d %H:%M:%S")
            print(f"Latest Activity: {latest_date}")


def show_listings_by_run(run_id: str):
    """Show all listings for a specific run."""
    with db_manager.get_session() as session:
        listings = session.query(ListingModel).filter(
            ListingModel.run_id == run_id
        ).order_by(ListingModel.scraped_at).all()
        
        if not listings:
            print(f"No listings found for run ID: {run_id}")
            return
        
        print(f"\nListings for run {run_id}:")
        print("-" * 120)
        print(f"{'Title':<50} {'Price':<15} {'Scraped At':<20} {'URL':<35}")
        print("-" * 120)
        
        for listing in listings:
            title = listing.title[:47] + "..." if len(listing.title) > 50 else listing.title
            scraped = listing.scraped_at.strftime("%Y-%m-%d %H:%M:%S")
            url = listing.url[:32] + "..." if len(listing.url) > 35 else listing.url
            print(f"{title:<50} {listing.price or 'N/A':<15} {scraped:<20} {url:<35}")


def main():
    parser = argparse.ArgumentParser(description="Query CarScout database")
    parser.add_argument(
        "--recent", 
        type=int, 
        default=24, 
        help="Show recent listings (default: last 24 hours)"
    )
    parser.add_argument(
        "--runs", 
        action="store_true", 
        help="Show summary of scraping runs"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show database statistics"
    )
    parser.add_argument(
        "--run-id", 
        type=str, 
        help="Show listings for a specific run ID"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Show all information"
    )
    
    args = parser.parse_args()
    
    if args.run_id:
        show_listings_by_run(args.run_id)
        return
    
    if args.all:
        show_database_stats()
        show_runs_summary()
        show_recent_listings(args.recent)
    else:
        if args.stats:
            show_database_stats()
        if args.runs:
            show_runs_summary()
        if args.recent:
            show_recent_listings(args.recent)
        
        # If no specific options, show stats by default
        if not any([args.stats, args.runs, args.recent]):
            show_database_stats()


if __name__ == "__main__":
    main()
