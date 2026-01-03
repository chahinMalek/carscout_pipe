from worker.tasks import process_vehicles

from infra.containers import Container


def main():
    container = Container()
    container.init_resources()
    process_vehicles.delay(run_id="05d7c6a2-522e-4c17-ab15-f9aed2491245")


if __name__ == "__main__":
    main()
