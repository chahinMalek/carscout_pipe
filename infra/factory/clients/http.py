from enum import Enum

import httpx
import requests

from infra.factory.logger import LoggerFactory
from infra.interfaces.cookie_provider import CookieProvider
from infra.interfaces.http import HttpClient


class ClientType(Enum):
    REQUESTS = "requests"
    HTTPX = "httpx"


class HttpClientFactory:
    def __init__(
        self,
        url: str,
        headers: dict,
        logger_factory: LoggerFactory,
        cookie_provider: CookieProvider,
        client_type: ClientType = ClientType.REQUESTS,
    ):
        self._url = url
        self._logger = logger_factory.create(__name__)
        self._cookie_provider = cookie_provider
        self._headers = headers
        self._client_type = client_type

    def create(self) -> HttpClient:
        cookies = self._cookie_provider.provide(self._url)
        if self._client_type == ClientType.HTTPX:
            return self._create_httpx_client(self._headers, cookies)
        else:  # by default returns a requests.Session object
            return self._create_requests_session(self._headers, cookies)

    def _create_requests_session(
        self, headers: dict, cookies: list[dict]
    ) -> requests.Session:
        session = requests.Session()
        session.headers.update(headers)
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])
        return session

    def _create_httpx_client(self, headers: dict, cookies: list[dict]) -> httpx.Client:
        return httpx.Client(
            headers=headers,
            cookies={cookie["name"]: cookie["value"] for cookie in cookies},
        )
