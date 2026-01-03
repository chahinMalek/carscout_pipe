from typing import Any, Protocol


class HttpClient(Protocol):
    """Protocol for HTTP clients (requests.Session, httpx.Client, etc.)"""

    headers: Any  # Header dict-like object

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def post(
        self,
        url: str,
        *,
        data: Any | None = None,
        json: Any | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def put(
        self,
        url: str,
        *,
        data: Any | None = None,
        json: Any | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def delete(
        self,
        url: str,
        *,
        headers: dict | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def patch(
        self,
        url: str,
        *,
        data: Any | None = None,
        json: Any | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any: ...

    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...

    def close(self) -> None: ...
