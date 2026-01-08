from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import WebDriverException

from infra.factory.webdriver import WebdriverFactory


class TestWebdriverFactory:
    @pytest.fixture
    def factory(self, mock_logger_factory):
        return WebdriverFactory(
            chrome_options=["--headless"],
            use_stealth=True,
            logger_factory=mock_logger_factory,
            timeout_seconds=10,
            chrome_binary_path="/path/to/chrome",
            chromedriver_path="/path/to/chromedriver",
        )

    @patch("infra.factory.webdriver.webdriver.Chrome")
    @patch("infra.factory.webdriver.Service")
    @patch("infra.factory.webdriver.Options")
    @patch("infra.factory.webdriver.stealth")
    @patch("infra.factory.webdriver.timeout")
    def test_create_success(
        self, mock_timeout, mock_stealth, mock_options, mock_service, mock_chrome, factory
    ):
        mock_timeout.return_value.__enter__.return_value = None
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        driver = factory.create()

        assert driver == mock_driver
        mock_options.assert_called_once()
        assert mock_options.return_value.binary_location == "/path/to/chrome"
        mock_options.return_value.add_argument.assert_called_with("--headless")
        mock_service.assert_called_once_with(executable_path="/path/to/chromedriver")
        mock_chrome.assert_called_once_with(
            service=mock_service.return_value, options=mock_options.return_value
        )
        mock_stealth.assert_called_once()

    @patch("infra.factory.webdriver.webdriver.Chrome")
    @patch("infra.factory.webdriver.timeout")
    def test_create_timeout_error(self, mock_timeout, mock_chrome, factory, mock_logger_factory):
        mock_timeout.side_effect = TimeoutError("Timed out")

        with pytest.raises(TimeoutError):
            factory.create()

        mock_logger = mock_logger_factory.create.return_value
        mock_logger.error.assert_called()

    @patch("infra.factory.webdriver.webdriver.Chrome")
    @patch("infra.factory.webdriver.timeout")
    def test_create_webdriver_exception(
        self, mock_timeout, mock_chrome, factory, mock_logger_factory
    ):
        mock_timeout.return_value.__enter__.return_value = None
        mock_chrome.side_effect = WebDriverException("Driver failed")

        with pytest.raises(WebDriverException):
            factory.create()

        mock_logger = mock_logger_factory.create.return_value
        mock_logger.error.assert_called()

    @patch("infra.factory.webdriver.webdriver.Chrome")
    @patch("infra.factory.webdriver.timeout")
    def test_create_unexpected_exception(
        self, mock_timeout, mock_chrome, factory, mock_logger_factory
    ):
        mock_timeout.return_value.__enter__.return_value = None
        mock_chrome.side_effect = Exception("Unexpected")

        with pytest.raises(Exception, match="Unexpected"):
            factory.create()

        mock_logger = mock_logger_factory.create.return_value
        mock_logger.error.assert_called()
