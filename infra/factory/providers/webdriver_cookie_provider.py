from infra.interfaces.cookie_provider import CookieProvider
from infra.factory.webdriver import WebdriverFactory


class WebdriverCookieProvider(CookieProvider):
    """Implements CookieProvider using a Selenium WebDriver instance."""

    def __init__(self, webdriver_factory: WebdriverFactory) -> None:
        self.webdriver_factory = webdriver_factory

    def provide(self, url: str) -> list[dict]:
        driver = self.webdriver_factory.create()
        try:
            driver.get(url)
            retrieved_cookies = driver.get_cookies()
            provide_cookies = [
                {"name": cookie["name"], "value": cookie["value"]}
                for cookie in retrieved_cookies
            ]
            return provide_cookies
        finally:
            driver.quit()
