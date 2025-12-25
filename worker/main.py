from celery import Celery

from infra.containers import Container

container = Container()
container.init_resources()  # create DB tables

# Get Redis URL from container config
REDIS_URL = container.config.redis.url.provided()

celery_app = Celery(
    "vehicle_scraper",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Load celery config if you want
# celery_app.conf.update(...)

container.wire(packages=["worker"])
