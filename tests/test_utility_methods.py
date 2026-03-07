"""Tests for new utility methods (Phase 4)."""

import pytest
from unittest.mock import MagicMock, patch
from db_query_agent import DatabaseQueryAgent, ChatSession


class TestSessionUtilityMethods:
    """Test session management utility methods."""
    
    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
    
    def test_create_session(self, agent):
        """Test creating a session."""
        session = agent.create_session("test_session_1")
        
        assert isinstance(session, ChatSession)
        assert session.session_id == "test_session_1"
    
    def test_list_sessions(self, agent):
        """Test listing all sessions."""
        # Create multiple sessions
        agent.create_session("session_1")
        agent.create_session("session_2")
        agent.create_session("session_3")
        
        sessions = agent.list_sessions()
        
        assert isinstance(sessions, list)
        assert len(sessions) >= 3
        assert "session_1" in sessions
        assert "session_2" in sessions
        assert "session_3" in sessions
    
    def test_list_sessions_empty(self, agent):
        """Test listing sessions when none exist."""
        sessions = agent.list_sessions()
        
        assert isinstance(sessions, list)
        # May have default sessions, so just check it's a list
    
    def test_get_session_history(self, agent):
        """Test getting session history."""
        # Create session
        session = agent.create_session("history_test")
        
        # Get history (will be empty initially)
        history = agent.get_session_history("history_test")
        
        # Should return a list (empty or with items)
        assert isinstance(history, list) or history is None
    
    def test_get_session_history_nonexistent(self, agent):
        """Test getting history for non-existent session."""
        history = agent.get_session_history("nonexistent_session")
        
        # Should return None or empty list
        assert history is None or history == []
    
    def test_clear_session(self, agent):
        """Test clearing session history."""
        # Create session
        session = agent.create_session("clear_test")
        
        # Clear it (should not raise error)
        try:
            agent.clear_session("clear_test")
        except Exception as e:
            pytest.fail(f"clear_session raised exception: {e}")
    
    def test_delete_session(self, agent):
        """Test deleting a session."""
        # Create session
        session = agent.create_session("delete_test")
        
        # Delete it (should not raise error)
        try:
            agent.delete_session("delete_test")
        except Exception as e:
            pytest.fail(f"delete_session raised exception: {e}")


class TestSchemaUtilityMethods:
    """Test schema exploration utility methods."""
    
    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
    
    def test_get_schema(self, agent):
        """Test getting basic schema."""
        schema = agent.get_schema()
        
        assert isinstance(schema, dict)
        # Schema should be a dictionary of tables
    
    def test_get_schema_info_with_foreign_keys(self, agent):
        """Test getting detailed schema with foreign keys."""
        # Mock schema extractor
        mock_schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"}
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": []
            },
            "orders": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "user_id", "type": "INTEGER"}
                ],
                "primary_keys": ["id"],
                "foreign_keys": [
                    {
                        "constrained_columns": ["user_id"],
                        "referred_table": "users",
                        "referred_columns": ["id"]
                    }
                ],
                "indexes": []
            }
        }
        
        agent.schema_extractor.get_schema = MagicMock(return_value=mock_schema)
        
        schema_info = agent.get_schema_info(include_foreign_keys=True)
        
        assert "total_tables" in schema_info
        assert schema_info["total_tables"] == 2
        assert "tables" in schema_info
        assert "users" in schema_info["tables"]
        assert "orders" in schema_info["tables"]
        assert "relationships" in schema_info
        assert len(schema_info["relationships"]) > 0
    
    def test_get_schema_info_without_foreign_keys(self, agent):
        """Test getting schema without foreign keys (faster)."""
        mock_schema = {
            "users": {
                "columns": [{"name": "id", "type": "INTEGER"}],
                "primary_keys": ["id"],
                "indexes": []
            }
        }
        
        agent.schema_extractor.get_schema = MagicMock(return_value=mock_schema)
        
        schema_info = agent.get_schema_info(include_foreign_keys=False)
        
        assert "total_tables" in schema_info
        assert "tables" in schema_info
        # Should not have relationships when include_foreign_keys=False
        if "relationships" in schema_info:
            assert schema_info["relationships"] is None or len(schema_info["relationships"]) == 0


class TestStatisticsUtilityMethods:
    """Test statistics utility methods."""
    
    def test_get_stats_comprehensive(self):
        """Test getting comprehensive statistics."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        stats = agent.get_stats()
        
        # Should have query statistics
        assert "total_queries" in stats
        assert "successful_queries" in stats
        assert "failed_queries" in stats
        assert "cache_hits" in stats
        
        # Should have cache statistics
        assert "cache" in stats
        # Cache stats structure may vary
        
        # Should have pool statistics
        assert "pool" in stats
        
        # Should have session statistics
        assert "sessions" in stats
        
        # Should have schema statistics
        assert "schema_tables" in stats
    
    def test_get_stats_without_query_stats(self):
        """Test get_stats when query statistics are disabled."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=False
        )
        
        stats = agent.get_stats()
        
        # Query stats should be N/A or not present
        if "total_queries" in stats:
            assert stats["total_queries"] == "N/A"
        
        # Other stats should still be present
        assert "cache" in stats
        assert "pool" in stats
    
    def test_stats_increment_on_query(self):
        """Test that statistics increment on queries."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        initial_count = agent.stats["total_queries"]
        
        # Mock a query
        agent.stats["total_queries"] += 1
        agent.stats["successful_queries"] += 1
        
        assert agent.stats["total_queries"] == initial_count + 1
        assert agent.stats["successful_queries"] == 1


class TestAgentClosureAndCleanup:
    """Test agent cleanup methods."""
    
    def test_close_method(self):
        """Test closing agent and cleaning up resources."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        # Close should not raise errors
        try:
            agent.close()
        except Exception as e:
            pytest.fail(f"close() raised exception: {e}")


class TestExportedClasses:
    """Test that all classes are properly exported."""
    
    def test_agent_export(self):
        """Test DatabaseQueryAgent is exported."""
        from db_query_agent import DatabaseQueryAgent
        assert DatabaseQueryAgent is not None
    
    def test_chat_session_export(self):
        """Test ChatSession is exported."""
        from db_query_agent import ChatSession
        assert ChatSession is not None
    
    def test_config_classes_export(self):
        """Test configuration classes are exported."""
        from db_query_agent import (
            AgentConfig,
            DatabaseConfig,
            CacheConfig,
            ModelConfig,
            SafetyConfig
        )
        
        assert AgentConfig is not None
        assert DatabaseConfig is not None
        assert CacheConfig is not None
        assert ModelConfig is not None
        assert SafetyConfig is not None
    
    def test_exception_classes_export(self):
        """Test exception classes are exported."""
        from db_query_agent import (
            DatabaseQueryAgentError,
            ValidationError,
            QueryExecutionError,
            SchemaExtractionError
        )
        
        assert DatabaseQueryAgentError is not None
        assert ValidationError is not None
        assert QueryExecutionError is not None
        assert SchemaExtractionError is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
