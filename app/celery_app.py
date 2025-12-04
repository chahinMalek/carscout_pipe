from celery import Celery

from infra.containers import Container


celery_app = Celery(
    "vehicle_scraper",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Load celery config if you want
# celery_app.conf.update(...)

container = Container()
container.init_resources()   # create DB tables
container.wire(packages=["tasks"])
