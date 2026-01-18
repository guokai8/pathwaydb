"""Token bucket rate limiter."""
import time
import threading
from typing import Optional


class RateLimiter:
    """Thread-safe token bucket rate limiter."""
    
    def __init__(self, rate: float, burst: Optional[int] = None):
        """
        Args:
            rate: Tokens per second
            burst: Maximum burst size (default: rate)
        """
        self.rate = rate
        self.burst = burst or int(rate)
        self.tokens = float(self.burst)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens, blocking if necessary.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = infinite)
        
        Returns:
            True if acquired, False if timeout
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
            
            if deadline is not None and time.monotonic() >= deadline:
                return False
            
            # Sleep until next token
            time.sleep(1.0 / self.rate)

