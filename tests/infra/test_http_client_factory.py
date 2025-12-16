from unittest.mock import Mock

import httpx
import pytest
import requests

from infra.factory.clients.http import ClientType, HttpClientFactory
from infra.interfaces.cookie_provider import CookieProvider


@pytest.mark.unit
class TestHttpClientFactory:
    @pytest.fixture
    def http_headers(self):
        return {
            "User-Agent": "TestBot/1.0",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

    @pytest.fixture
    def mock_cookie_provider(self):
        provider = Mock(spec=CookieProvider)
        provider.provide.return_value = [
            {"name": "session_id", "value": "abc123"},
            {"name": "user_token", "value": "xyz789"},
        ]
        return provider

    @pytest.fixture
    def factory(self, mock_logger_factory, mock_cookie_provider, http_headers):
        return HttpClientFactory(
            url="https://example.com",
            headers=http_headers,
            logger_factory=mock_logger_factory,
            cookie_provider=mock_cookie_provider,
            client_type=ClientType.REQUESTS,
        )

    def test_create_requests_session_by_default(self, factory):
        client = factory.create()
        assert isinstance(client, requests.Session)

    def test_create_requests_session_headers(self, factory, http_headers):
        client = factory.create()
        assert client.headers["User-Agent"] == http_headers["User-Agent"]
        assert client.headers["Accept"] == http_headers["Accept"]
        assert client.headers["Connection"] == http_headers["Connection"]

    def test_create_requests_session_cookies(self, factory, mock_cookie_provider):
        client = factory.create()

        # check if provide was called when http client was created
        mock_cookie_provider.provide.assert_called_once_with("https://example.com")

        # assert all cookies are stored in the client
        provided_cookies = mock_cookie_provider.provide()
        for cookie in provided_cookies:
            assert client.cookies[cookie["name"]] == cookie["value"]

    def test_create_httpx_client(self, mock_logger_factory, mock_cookie_provider, http_headers):
        factory = HttpClientFactory(
            url="https://example.com",
            headers=http_headers,
            logger_factory=mock_logger_factory,
            cookie_provider=mock_cookie_provider,
            client_type=ClientType.HTTPX,
        )
        client = factory.create()
        assert isinstance(client, httpx.Client)

    def test_create_httpx_client_headers(
        self, mock_logger_factory, mock_cookie_provider, http_headers
    ):
        factory = HttpClientFactory(
            url="https://example.com",
            headers=http_headers,
            logger_factory=mock_logger_factory,
            cookie_provider=mock_cookie_provider,
            client_type=ClientType.HTTPX,
        )
        client = factory.create()
        assert client.headers["User-Agent"] == http_headers["User-Agent"]
        assert client.headers["Accept"] == http_headers["Accept"]
        assert client.headers["Connection"] == http_headers["Connection"]

    def test_create_httpx_client_cookies(self, mock_logger_factory, mock_cookie_provider):
        factory = HttpClientFactory(
            url="https://example.com",
            headers={},
            logger_factory=mock_logger_factory,
            cookie_provider=mock_cookie_provider,
            client_type=ClientType.HTTPX,
        )
        client = factory.create()

        # check if provide was called when http client was created
        mock_cookie_provider.provide.assert_called_once_with("https://example.com")

        # assert all cookies are stored in the client
        provided_cookies = mock_cookie_provider.provide()
        for cookie in provided_cookies:
            assert client.cookies[cookie["name"]] == cookie["value"]
