from unittest.mock import Mock

import pytest

from infra.factory.providers.webdriver_cookie_provider import WebdriverCookieProvider
from infra.factory.webdriver import WebdriverFactory


class TestWebdriverCookieProvider:
    @pytest.fixture
    def mock_webdriver(self):
        driver = Mock()
        driver.get_cookies.return_value = [{"name": "some_cookie", "value": "some_value"}]
        return driver

    @pytest.fixture
    def mock_webdriver_factory(self, mock_webdriver):
        factory = Mock(spec=WebdriverFactory)
        factory.create.return_value = mock_webdriver
        return factory

    def test_provide_returns_cookies_correctly(self, mock_webdriver_factory, mock_webdriver):
        url = "https://example.com"
        cookie_provider = WebdriverCookieProvider(mock_webdriver_factory)
        provided = cookie_provider.provide(url)

        assert provided == [{"name": "some_cookie", "value": "some_value"}]
        mock_webdriver_factory.create.assert_called_once()
        mock_webdriver.get.assert_called_once_with(url)
        mock_webdriver.get_cookies.assert_called_once()
        mock_webdriver.quit.assert_called_once()

    def test_provide_quits_on_error(self, mock_webdriver_factory, mock_webdriver):
        mock_webdriver.get.side_effect = Exception("Browser error")
        cookie_provider = WebdriverCookieProvider(mock_webdriver_factory)

        with pytest.raises(Exception, match="Browser error"):
            cookie_provider.provide("https://example.com")

        mock_webdriver.quit.assert_called_once()
