"""Tests for cache_manager module."""

import pytest
import time
from db_query_agent.cache_manager import CacheManager


class TestCacheManager:
    """Test CacheManager class."""
    
    def test_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager(schema_ttl=100, query_ttl=50, llm_ttl=75)
        assert cache.schema_ttl == 100
        assert cache.query_ttl == 50
        assert cache.llm_ttl == 75
        assert len(cache._cache) == 0
    
    def test_set_and_get(self, cache_manager):
        """Test basic set and get operations."""
        cache_manager.set("test_key", "test_value", ttl=60)
        value = cache_manager.get("test_key")
        assert value == "test_value"
    
    def test_get_nonexistent(self, cache_manager):
        """Test getting non-existent key."""
        value = cache_manager.get("nonexistent")
        assert value is None
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = CacheManager(schema_ttl=1, query_ttl=1, llm_ttl=1)
        cache.set("test_key", "test_value", ttl=1)
        
        # Should exist immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("test_key") is None
    
    def test_delete(self, cache_manager):
        """Test cache deletion."""
        cache_manager.set("test_key", "test_value", ttl=60)
        assert cache_manager.get("test_key") == "test_value"
        
        cache_manager.delete("test_key")
        assert cache_manager.get("test_key") is None
    
    def test_clear(self, cache_manager):
        """Test clearing all cache."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.set("key2", "value2", ttl=60)
        
        assert len(cache_manager._cache) == 2
        
        cache_manager.clear()
        assert len(cache_manager._cache) == 0
    
    def test_schema_caching(self, cache_manager):
        """Test schema-specific caching."""
        schema = {"users": {"columns": ["id", "name"]}}
        cache_manager.set_schema("postgresql://localhost/test", schema)
        
        cached = cache_manager.get_schema("postgresql://localhost/test")
        assert cached == schema
    
    def test_query_result_caching(self, cache_manager):
        """Test query result caching."""
        sql = "SELECT * FROM users"
        results = [(1, "Alice"), (2, "Bob")]
        
        cache_manager.set_query_result(sql, results)
        cached = cache_manager.get_query_result(sql)
        
        assert cached == results
    
    def test_llm_response_caching(self, cache_manager):
        """Test LLM response caching."""
        query = "how many users"
        schema_hash = "abc123"
        response = "SELECT COUNT(*) FROM users"
        
        cache_manager.set_llm_response(query, schema_hash, response)
        cached = cache_manager.get_llm_response(query, schema_hash)
        
        assert cached == response
    
    def test_get_stats(self, cache_manager):
        """Test cache statistics."""
        cache_manager.set("key1", "value1", ttl=60)
        cache_manager.set("key2", "value2", ttl=60)
        
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
    
    def test_stats_with_expired(self):
        """Test statistics with expired entries."""
        cache = CacheManager(schema_ttl=1, query_ttl=1, llm_ttl=1)
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=60)
        
        time.sleep(1.1)
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["active_entries"] == 1
