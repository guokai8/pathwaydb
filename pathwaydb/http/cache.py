"""Disk-based HTTP cache."""
import hashlib
import json
import gzip
import time
from pathlib import Path
from typing import Optional, Dict, Any
from ..core.exceptions import CacheError


class DiskCache:
    """Simple disk cache for HTTP responses."""
    
    def __init__(self, cache_dir: str, max_age_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_days * 86400
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path."""
        hash_hex = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_hex[:2]}" / f"{hash_hex}.json.gz"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        path = self._key_to_path(key)
        
        if not path.exists():
            return None
        
        # Check age
        age = time.time() - path.stat().st_mtime
        if age > self.max_age_seconds:
            path.unlink()
            return None
        
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise CacheError(f"Failed to read cache: {e}")
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Cache response."""
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                json.dump(value, f)
        except (OSError, TypeError) as e:
            raise CacheError(f"Failed to write cache: {e}")
    
    def clear(self) -> int:
        """Clear all cache files."""
        count = 0
        for path in self.cache_dir.rglob("*.json.gz"):
            path.unlink()
            count += 1
        return count
    
    def size(self) -> int:
        """Get cache size in bytes."""
        return sum(p.stat().st_size for p in self.cache_dir.rglob("*.json.gz"))

