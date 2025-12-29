from infra.containers import Container
from infra.settings import Settings


def bootstrap_container() -> Container:
    container = Container()
    settings = Settings()
    container.config.from_pydantic(settings)
    return container
