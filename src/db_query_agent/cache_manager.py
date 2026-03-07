"""Multi-layer caching system for schema, queries, and LLM responses."""

import time
import hashlib
import json
from typing import Any, Optional, Dict
from db_query_agent.exceptions import CacheError
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Multi-layer cache with TTL support."""
    
    def __init__(
        self,
        schema_ttl: int = 3600,
        query_ttl: int = 300,
        llm_ttl: int = 3600
    ):
        """
        Initialize cache manager.
        
        Args:
            schema_ttl: Schema cache TTL in seconds
            query_ttl: Query result cache TTL in seconds
            llm_ttl: LLM response cache TTL in seconds
        """
        self.schema_ttl = schema_ttl
        self.query_ttl = query_ttl
        self.llm_ttl = llm_ttl
        
        # In-memory cache (L1)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Create cache key from data."""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if "timestamp" not in entry or "ttl" not in entry:
            return True
        
        elapsed = time.time() - entry["timestamp"]
        return elapsed > entry["ttl"]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        if self._is_expired(entry):
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        self._cache[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    # Convenience methods for specific cache types
    
    def get_schema(self, database_url: str) -> Optional[Dict[str, Any]]:
        """Get cached schema."""
        key = self._make_key("schema", database_url)
        return self.get(key)
    
    def set_schema(self, database_url: str, schema: Dict[str, Any]) -> None:
        """Cache schema."""
        key = self._make_key("schema", database_url)
        self.set(key, schema, self.schema_ttl)
    
    def get_query_result(self, sql: str) -> Optional[Any]:
        """Get cached query result."""
        key = self._make_key("query", sql)
        return self.get(key)
    
    def set_query_result(self, sql: str, result: Any) -> None:
        """Cache query result."""
        key = self._make_key("query", sql)
        self.set(key, result, self.query_ttl)
    
    def get_llm_response(self, query: str, schema_hash: str) -> Optional[str]:
        """Get cached LLM response."""
        key = self._make_key("llm", f"{query}:{schema_hash}")
        return self.get(key)
    
    def set_llm_response(self, query: str, schema_hash: str, response: str) -> None:
        """Cache LLM response."""
        key = self._make_key("llm", f"{query}:{schema_hash}")
        self.set(key, response, self.llm_ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries
        }
