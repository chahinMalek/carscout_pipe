from typing import Protocol, Any, Optional


class HttpClient(Protocol):
    """Protocol for HTTP clients (requests.Session, httpx.Client, etc.)"""
    
    headers: Any  # Header dict-like object
    
    def get(
        self,
        url: str,
        *,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        ...
    
    def post(
        self,
        url: str,
        *,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        ...
    
    def put(
        self,
        url: str,
        *,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        ...
    
    def delete(
        self,
        url: str,
        *,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        ...
    
    def patch(
        self,
        url: str,
        *,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        ...
    
    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> Any:
        ...
    
    def close(self) -> None:
        ...
