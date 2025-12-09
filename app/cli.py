from infra.containers import Container
from infra.db.repositories.listings import SqlAlchemyListingRepository


def main():
    container = Container()
    container.init_resources()

    listing_repository: SqlAlchemyListingRepository = container.listing_repository()
    run_id = listing_repository.find_latest_run()
    print(f"Latest run_id: {run_id}")
    listings = listing_repository.search_with_run_id(run_id)
    print(f"Number of found listings: {len(listings)}")


if __name__ == "__main__":
    main()
