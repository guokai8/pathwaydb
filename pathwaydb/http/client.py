"""HTTP client with retry and caching."""
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict
from .cache import DiskCache
from .ratelimit import RateLimiter
from ..core.exceptions import NetworkError, RateLimitError


class HTTPClient:
    """HTTP client with retry, rate limiting, and caching."""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        rate_limit: float = 3.0,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = "pathwaydb/1.0"
    ):
        self.cache = DiskCache(cache_dir) if cache_dir else None
        self.rate_limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        GET request with retry and caching.
        
        Args:
            url: Request URL
            params: Query parameters
            use_cache: Whether to use cache
            headers: Additional headers
        
        Returns:
            Response body as string
        
        Raises:
            NetworkError: Request failed after retries
            RateLimitError: Rate limit acquisition timeout
        """
        # Build full URL
        if params:
            query = urllib.parse.urlencode(params)
            full_url = f"{url}?{query}"
        else:
            full_url = url
        
        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(full_url)
            if cached:
                return cached['body']
        
        # Rate limit
        if not self.rate_limiter.acquire(timeout=60):
            raise RateLimitError("Rate limit timeout")
        
        # Retry loop
        last_error = None
        for attempt in range(self.max_retries):
            try:
                req_headers = {'User-Agent': self.user_agent}
                if headers:
                    req_headers.update(headers)
                
                request = urllib.request.Request(full_url, headers=req_headers)
                
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = response.read().decode('utf-8')
                
                # Cache success
                if self.cache:
                    self.cache.set(full_url, {'body': body})
                
                return body
            
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise NetworkError(f"Not found: {full_url}")
                elif e.code == 429:
                    raise RateLimitError(f"Rate limit from server: {full_url}")
                last_error = e
            
            except (urllib.error.URLError, TimeoutError) as e:
                last_error = e
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)
        
        raise NetworkError(f"Request failed after {self.max_retries} attempts: {last_error}")

