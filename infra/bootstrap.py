from pathlib import Path

from infra.containers import Container
from infra.settings import Settings


def bootstrap_container() -> Container:
    container = Container()

    settings = Settings()

    # load config from yaml
    config_path = Path(settings.project_root) / f"infra/configs/{settings.environment}.yml"
    container.config.from_yaml(str(config_path))

    # override with provided environment variables
    container.config.from_pydantic(settings)
    return container
