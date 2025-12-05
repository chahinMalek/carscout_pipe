from infra.containers import Container
from tasks.scraping import process_vehicles


def main():
    container = Container()
    container.init_resources()
    process_vehicles.delay()


if __name__ == "__main__":
    main()
