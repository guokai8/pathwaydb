"""Custom exceptions."""


class BioannoError(Exception):
    """Base exception."""
    pass


class NetworkError(BioannoError):
    """Network request failed."""
    pass


class ParseError(BioannoError):
    """Failed to parse response."""
    pass


class NotFoundError(BioannoError):
    """Resource not found."""
    pass


class RateLimitError(BioannoError):
    """Rate limit exceeded."""
    pass


class CacheError(BioannoError):
    """Cache operation failed."""
    pass


class StorageError(BioannoError):
    """Storage/database operation failed."""
    pass

