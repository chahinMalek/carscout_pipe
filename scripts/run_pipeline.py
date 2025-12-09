from infra.containers import Container
from tasks.scraping import pipeline


def main():
    container = Container()
    container.init_resources()
    pipeline.delay()


if __name__ == "__main__":
    main()
