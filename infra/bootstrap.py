import os

from infra.containers import Container
from infra.settings import Settings


def bootstrap_container() -> Container:
    container = Container()

    settings = Settings()
    container.config.from_pydantic(settings)
    config_path = os.path.join(
        settings.project_root,
        f"infra/configs/{settings.environment}.yml",
    )
    container.config.from_yaml(config_path)
    return container
