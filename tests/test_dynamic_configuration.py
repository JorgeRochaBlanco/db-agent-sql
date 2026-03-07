"""Tests for dynamic configuration system (Phase 4)."""

import pytest
import os
from unittest.mock import patch, MagicMock
from db_query_agent import DatabaseQueryAgent
from db_query_agent.config import (
    AgentConfig,
    DatabaseConfig,
    CacheConfig,
    ModelConfig,
    SafetyConfig
)


class TestDynamicConfiguration:
    """Test dynamic configuration with parameter, .env, and default fallback."""
    
    def test_direct_parameter_configuration(self):
        """Test configuration via direct parameters."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            fast_model="gpt-4o-mini",
            balanced_model="gpt-4.1-mini",
            complex_model="gpt-4.1",
            enable_cache=True,
            read_only=True,
            enable_streaming=False,
            enable_statistics=True
        )
        
        assert agent.config.openai_api_key == "sk-test-key"
        assert agent.config.model.fast_model == "gpt-4o-mini"
        assert agent.config.cache.enabled is True
        assert agent.config.safety.read_only is True
        assert agent.enable_streaming is False
        assert agent.enable_statistics is True
    
    @patch.dict(os.environ, {
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "sk-env-key",
        "FAST_MODEL": "gpt-4o-mini",
        "CACHE_ENABLED": "true",
        "READ_ONLY": "false",
        "ENABLE_STREAMING": "true"
    })
    def test_env_configuration(self):
        """Test configuration from environment variables."""
        agent = DatabaseQueryAgent.from_env()
        
        assert agent.config.openai_api_key == "sk-env-key"
        assert agent.config.model.fast_model == "gpt-4o-mini"
        assert agent.config.cache.enabled is True
        assert agent.config.safety.read_only is False
        assert agent.enable_streaming is True
    
    @patch.dict(os.environ, {
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "sk-env-key",
        "FAST_MODEL": "gpt-4o-mini",
        "ENABLE_STREAMING": "false"
    })
    def test_parameter_overrides_env(self):
        """Test that direct parameters override .env values."""
        agent = DatabaseQueryAgent.from_env(
            fast_model="gpt-4.1",  # Override env
            enable_streaming=True,  # Override env
            enable_statistics=False
        )
        
        assert agent.config.model.fast_model == "gpt-4.1"  # Overridden
        assert agent.enable_streaming is True  # Overridden
        assert agent.enable_statistics is False
    
    def test_default_values(self):
        """Test default configuration values."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        # Check defaults
        assert agent.config.model.strategy == "adaptive"
        assert agent.config.cache.enabled is True
        assert agent.config.safety.read_only is True
        assert agent.enable_streaming is False  # Default is False
        assert agent.enable_statistics is True  # Default is True
    
    def test_missing_required_credentials(self):
        """Test that missing credentials raise errors when using from_env()."""
        # from_env() validates required credentials
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                DatabaseQueryAgent.from_env()
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL"):
                DatabaseQueryAgent.from_env()


class TestConfigurationClasses:
    """Test configuration dataclasses."""
    
    def test_model_config(self):
        """Test ModelConfig."""
        config = ModelConfig(
            strategy="adaptive",
            fast_model="gpt-4o-mini",
            balanced_model="gpt-4.1-mini",
            complex_model="gpt-4.1"
        )
        
        assert config.strategy == "adaptive"
        assert config.fast_model == "gpt-4o-mini"
    
    def test_cache_config(self):
        """Test CacheConfig."""
        config = CacheConfig(
            enabled=True,
            backend="memory",
            schema_ttl=3600,
            query_ttl=300
        )
        
        assert config.enabled is True
        assert config.backend == "memory"
        assert config.schema_ttl == 3600
    
    def test_safety_config(self):
        """Test SafetyConfig."""
        config = SafetyConfig(
            read_only=True,
            allowed_tables=["users", "orders"],
            max_query_timeout=30
        )
        
        assert config.read_only is True
        assert config.allowed_tables == ["users", "orders"]
        assert config.max_query_timeout == 30
    
    def test_database_config(self):
        """Test DatabaseConfig."""
        config = DatabaseConfig(
            url="sqlite:///:memory:",
            pool_size=10,
            max_overflow=20
        )
        
        assert config.url == "sqlite:///:memory:"
        assert config.pool_size == 10
        assert config.max_overflow == 20


class TestStatisticsConfiguration:
    """Test statistics tracking configuration."""
    
    def test_statistics_enabled(self):
        """Test statistics when enabled."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        assert agent.enable_statistics is True
        assert agent.stats is not None
        assert "total_queries" in agent.stats
        assert agent.stats["total_queries"] == 0
    
    def test_statistics_disabled(self):
        """Test statistics when disabled."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=False
        )
        
        assert agent.enable_statistics is False
        assert agent.stats is None
    
    def test_get_stats_with_statistics_enabled(self):
        """Test get_stats() when statistics are enabled."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        stats = agent.get_stats()
        
        # Should have query stats
        assert "total_queries" in stats
        assert "successful_queries" in stats
        assert "failed_queries" in stats
        assert "cache_hits" in stats
        
        # Should have other stats
        assert "cache" in stats
        assert "pool" in stats
        assert "sessions" in stats
    
    def test_get_stats_without_statistics(self):
        """Test get_stats() when statistics are disabled."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=False
        )
        
        stats = agent.get_stats()
        
        # Should not have query stats
        assert "total_queries" not in stats or stats["total_queries"] == "N/A"
        
        # Should still have other stats
        assert "cache" in stats
        assert "pool" in stats


class TestStreamingConfiguration:
    """Test streaming configuration."""
    
    def test_streaming_disabled_by_default(self):
        """Test that streaming is disabled by default."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        assert agent.enable_streaming is False
    
    def test_streaming_enabled_via_parameter(self):
        """Test enabling streaming via parameter."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True
        )
        
        assert agent.enable_streaming is True
    
    @patch.dict(os.environ, {
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "sk-test-key",
        "ENABLE_STREAMING": "true"
    })
    def test_streaming_enabled_via_env(self):
        """Test enabling streaming via environment variable."""
        agent = DatabaseQueryAgent.from_env()
        
        assert agent.enable_streaming is True
    
    @pytest.mark.asyncio
    async def test_query_stream_method_exists(self):
        """Test that query_stream method exists."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True
        )
        
        assert hasattr(agent, "query_stream")
        assert callable(agent.query_stream)


class TestSessionConfiguration:
    """Test session configuration."""
    
    def test_session_backend_default(self):
        """Test default session backend."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        assert agent.session_backend == "sqlite"
    
    def test_session_backend_custom(self):
        """Test custom session backend."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            session_backend="memory"
        )
        
        assert agent.session_backend == "memory"
    
    def test_session_db_path_custom(self):
        """Test custom session database path."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            session_db_path="./custom_sessions.db"
        )
        
        assert agent.session_db_path == "./custom_sessions.db"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
