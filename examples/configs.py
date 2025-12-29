from pprint import pprint

from infra.containers import Container

if __name__ == "__main__":
    # play around with the environment variables and/or env files
    container = Container.create_and_patch()
    pprint(container.config.provided())
