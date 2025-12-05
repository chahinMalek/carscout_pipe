from infra.containers import Container
from tasks.scraping import process_vehicles


def main():
    container = Container()
    container.init_resources()

    http_client = container.http_client_factory().create()


if __name__ == "__main__":
    main()
