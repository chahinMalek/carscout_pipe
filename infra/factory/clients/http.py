from enum import Enum
import requests
import httpx

from infra.factory.logger import LoggerFactory
from infra.factory.webdriver import WebdriverFactory
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
        webdriver_factory: WebdriverFactory,
        client_type: ClientType = ClientType.REQUESTS,
    ):
        self._url = url
        self._logger = logger_factory.create(__name__)
        self._webdriver_factory = webdriver_factory
        self._headers = headers
        self._client_type = client_type

    def create(self) -> HttpClient:
        cookies = self._retrieve_cookies()

        token = self._extract_xsrf_token(cookies)
        if not token:
            self._logger.error("Failed to extract XSRF-TOKEN from cookies")
            raise ValueError("Failed to fetch auth token.")
        self._logger.info("Successfully obtained XSRF token")

        headers = {
            **self._headers,
            "referer": self._url,
            "X-Xsrf-Token": token,
        }

        if self._client_type == ClientType.HTTPX:
            return self._create_httpx_client(headers, cookies)
        else:
            return self._create_requests_session(headers, cookies)

    def _retrieve_cookies(self) -> list[dict]:
        driver = self._webdriver_factory.create()
        driver.get(self._url)
        return driver.get_cookies()

    def _extract_xsrf_token(self, cookies: list) -> str | None:
        for cookie in cookies:
            if cookie["name"] == "XSRF-TOKEN":
                return cookie["value"]
        return None

    def _create_requests_session(self, headers: dict, cookies: list) -> requests.Session:
        session = requests.Session()
        session.headers.update(headers)
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])
        return session

    def _create_httpx_client(self, headers: dict, cookies: list) -> httpx.Client:
        return httpx.Client(
            headers=headers,
            cookies={cookie["name"]: cookie["value"] for cookie in cookies},
        )
