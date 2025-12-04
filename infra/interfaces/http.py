from typing import Protocol, Any, Optional, Union


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
        """Send a GET request"""
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
        """Send a POST request"""
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
        """Send a PUT request"""
        ...
    
    def delete(
        self,
        url: str,
        *,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        """Send a DELETE request"""
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
        """Send a PATCH request"""
        ...
    
    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any
    ) -> Any:
        """Send a request with the given method"""
        ...
    
    def close(self) -> None:
        """Close the client and release resources"""
        ...
