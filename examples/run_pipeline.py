from worker.tasks import pipeline

from infra.containers import Container


def main():
    container = Container()
    container.init_resources()
    pipeline.delay()


if __name__ == "__main__":
    main()
