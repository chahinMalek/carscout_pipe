from infra.containers import Container


def main():
    container = Container()
    container.init_resources()

    http_client = container.http_client_factory().create()

    url = "https://olx.ba/api/listings/72700619"
    res = http_client.get(url)
    print(res.json())


if __name__ == "__main__":
    main()
