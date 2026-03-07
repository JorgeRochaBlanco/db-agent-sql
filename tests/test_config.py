"""Tests for config module."""

import pytest
import os
from db_query_agent.config import (
    DatabaseConfig,
    CacheConfig,
    ModelConfig,
    SafetyConfig,
    AgentConfig
)


class TestDatabaseConfig:
    """Test DatabaseConfig class."""
    
    def test_initialization(self):
        """Test database config initialization."""
        config = DatabaseConfig(url="sqlite:///:memory:")
        assert config.url == "sqlite:///:memory:"
        assert config.pool_size == 10
        assert config.max_overflow == 20
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = DatabaseConfig(
            url="postgresql://localhost/test",
            pool_size=5,
            max_overflow=10
        )
        assert config.pool_size == 5
        assert config.max_overflow == 10


class TestCacheConfig:
    """Test CacheConfig class."""
    
    def test_defaults(self):
        """Test default cache configuration."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.backend == "memory"
        assert config.schema_ttl == 3600
        assert config.query_ttl == 300
        assert config.llm_ttl == 3600
    
    def test_custom_values(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            backend="redis",
            schema_ttl=7200,
            redis_url="redis://localhost:6379"
        )
        assert config.backend == "redis"
        assert config.schema_ttl == 7200
        assert config.redis_url == "redis://localhost:6379"


class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_defaults(self):
        """Test default model configuration."""
        config = ModelConfig()
        assert config.strategy == "adaptive"
        assert config.fast_model == "gpt-4o-mini"
        assert config.balanced_model == "gpt-4.1-mini"
        assert config.temperature == 0.0
    
    def test_custom_values(self):
        """Test custom model configuration."""
        config = ModelConfig(
            strategy="fixed",
            fast_model="gpt-3.5-turbo",
            temperature=0.5
        )
        assert config.strategy == "fixed"
        assert config.fast_model == "gpt-3.5-turbo"
        assert config.temperature == 0.5


class TestSafetyConfig:
    """Test SafetyConfig class."""
    
    def test_defaults(self):
        """Test default safety configuration."""
        config = SafetyConfig()
        assert config.read_only is True
        assert config.allowed_tables is None
        assert config.blocked_tables is None
        assert config.max_query_timeout == 30
    
    def test_custom_values(self):
        """Test custom safety configuration."""
        config = SafetyConfig(
            read_only=False,
            allowed_tables=["users", "orders"],
            blocked_tables=["admin"],
            max_query_timeout=60
        )
        assert config.read_only is False
        assert config.allowed_tables == ["users", "orders"]
        assert config.blocked_tables == ["admin"]
        assert config.max_query_timeout == 60


class TestAgentConfig:
    """Test AgentConfig class."""
    
    def test_initialization(self):
        """Test agent config initialization."""
        config = AgentConfig(
            openai_api_key="test-key",
            database=DatabaseConfig(url="sqlite:///:memory:")
        )
        assert config.openai_api_key == "test-key"
        assert config.database.url == "sqlite:///:memory:"
        assert config.cache.enabled is True
        assert config.model.strategy == "adaptive"
        assert config.safety.read_only is True
    
    def test_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("CACHE_BACKEND", "redis")
        monkeypatch.setenv("FAST_MODEL", "gpt-3.5-turbo")
        
        config = AgentConfig.from_env()
        assert config.openai_api_key == "test-key"
        assert config.database.url == "sqlite:///:memory:"
        assert config.cache.backend == "redis"
        assert config.model.fast_model == "gpt-3.5-turbo"
    
    def test_from_env_missing_key(self, monkeypatch):
        """Test error when API key is missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            AgentConfig.from_env()
    
    def test_from_env_missing_database(self, monkeypatch):
        """Test error when database URL is missing."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        
        with pytest.raises(ValueError, match="DATABASE_URL"):
            AgentConfig.from_env()
