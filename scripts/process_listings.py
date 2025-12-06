from infra.containers import Container
from tasks.scraping import process_listings


def main():
    container = Container()
    container.init_resources()
    process_listings.delay()


if __name__ == "__main__":
    main()
