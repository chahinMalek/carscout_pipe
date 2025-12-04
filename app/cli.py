from infra.containers import Container
from infra.db.repositories.listings import SqlAlchemyListingRepository


def main():
    container = Container()
    container.init_resources()

    listing_repository: SqlAlchemyListingRepository = container.listing_repository()
    run_id = listing_repository.get_latest_run()
    listings = listing_repository.find_listings_for_run_id(run_id)
    print(len(listings))


if __name__ == "__main__":
    main()
