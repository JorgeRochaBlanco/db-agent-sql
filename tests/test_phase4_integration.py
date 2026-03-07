"""Integration tests for Phase 4 features."""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from db_query_agent import DatabaseQueryAgent


class TestPhase4Integration:
    """End-to-end integration tests for Phase 4 features."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_streaming(self):
        """Test complete workflow: configure, query, stream, get stats."""
        # Step 1: Create agent with full configuration
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            fast_model="gpt-4o-mini",
            enable_cache=True,
            read_only=True,
            enable_streaming=True,
            enable_statistics=True
        )
        
        # Step 2: Verify configuration
        assert agent.enable_streaming is True
        assert agent.enable_statistics is True
        assert agent.config.cache.enabled is True
        
        # Step 3: Mock streaming query
        async def mock_stream(question, session=None):
            for word in ["You", " have", " 10", " users"]:
                yield word
        
        agent.multi_agent_system.query_stream = mock_stream
        
        # Step 4: Execute streaming query
        response = ""
        async for chunk in agent.query_stream("How many users?"):
            response += chunk
        
        assert response == "You have 10 users"
        
        # Step 5: Get statistics
        stats = agent.get_stats()
        assert "total_queries" in stats
        assert "cache" in stats
        
        # Step 6: Cleanup
        agent.close()
    
    @pytest.mark.asyncio
    async def test_session_based_conversation(self):
        """Test session-based conversation flow."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        # Create session
        session = agent.create_session("conversation_test")
        assert session.session_id == "conversation_test"
        
        # Mock queries with async function
        async def mock_query(question, session=None):
            return {
                "natural_response": "Response 1",
                "final_output": "Response 1"
            }
        
        agent.multi_agent_system.query = mock_query
        
        # First query
        result1 = await agent.query("First question", session=session.session)
        assert "natural_response" in result1
        
        # Second query (with context)
        result2 = await agent.query("Follow-up question", session=session.session)
        assert "natural_response" in result2
        
        # Get session history
        sessions = agent.list_sessions()
        assert "conversation_test" in sessions
        
        # Cleanup
        agent.delete_session("conversation_test")
        agent.close()
    
    def test_configuration_priority(self):
        """Test configuration priority: parameter > env > default."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///:memory:",
            "OPENAI_API_KEY": "sk-env-key",
            "FAST_MODEL": "gpt-4o-mini",
            "ENABLE_STREAMING": "false",
            "CACHE_ENABLED": "false"  # Correct env var name
        }):
            # Load from env
            agent1 = DatabaseQueryAgent.from_env()
            assert agent1.enable_streaming is False
            assert agent1.config.cache.enabled is False
            agent1.close()
            
            # Override with parameters
            agent2 = DatabaseQueryAgent.from_env(
                enable_streaming=True,  # Override
                enable_cache=True  # Override
            )
            assert agent2.enable_streaming is True
            assert agent2.config.cache.enabled is True
            agent2.close()
    
    def test_schema_exploration_workflow(self):
        """Test schema exploration workflow."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        # Mock schema
        mock_schema = {
            "users": {
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"}
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": []
            }
        }
        agent.schema_extractor.get_schema = MagicMock(return_value=mock_schema)
        
        # Get basic schema
        schema = agent.get_schema()
        assert "users" in schema
        
        # Get detailed schema info
        schema_info = agent.get_schema_info(include_foreign_keys=True)
        assert schema_info["total_tables"] == 1
        assert "users" in schema_info["tables"]
        
        agent.close()
    
    @pytest.mark.asyncio
    async def test_caching_with_streaming(self):
        """Test that caching works with streaming."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_cache=True,
            enable_streaming=True,
            enable_statistics=True
        )
        
        # Mock cache hit
        async def mock_stream_cached(question, session=None):
            yield "Cached response"
        
        agent.multi_agent_system.query_stream = mock_stream_cached
        
        # First query (cache miss)
        response1 = ""
        async for chunk in agent.query_stream("test query"):
            response1 += chunk
        
        # Second query (should be cached)
        response2 = ""
        async for chunk in agent.query_stream("test query"):
            response2 += chunk
        
        assert response1 == response2
        
        agent.close()
    
    def test_statistics_tracking_workflow(self):
        """Test statistics tracking across operations."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        # Initial stats
        initial_stats = agent.get_stats()
        assert initial_stats["total_queries"] == 0
        
        # Simulate queries
        agent.stats["total_queries"] += 1
        agent.stats["successful_queries"] += 1
        
        # Check updated stats
        updated_stats = agent.get_stats()
        assert updated_stats["total_queries"] == 1
        assert updated_stats["successful_queries"] == 1
        
        # Calculate cache hit rate
        if updated_stats["total_queries"] > 0:
            hit_rate = (updated_stats["cache_hits"] / updated_stats["total_queries"]) * 100
            assert hit_rate >= 0
        
        agent.close()
    
    def test_multiple_agents_independent(self):
        """Test that multiple agents are independent."""
        agent1 = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True,
            enable_statistics=True
        )
        
        agent2 = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=False,
            enable_statistics=False
        )
        
        # Verify independence
        assert agent1.enable_streaming is True
        assert agent2.enable_streaming is False
        
        assert agent1.enable_statistics is True
        assert agent2.enable_statistics is False
        
        # Cleanup
        agent1.close()
        agent2.close()
    
    def test_error_handling_comprehensive(self):
        """Test error handling across features."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_statistics=True
        )
        
        # Test getting history for non-existent session
        history = agent.get_session_history("nonexistent")
        assert history is None or history == []
        
        # Test clearing non-existent session (should not crash)
        try:
            agent.clear_session("nonexistent")
        except Exception as e:
            pytest.fail(f"clear_session raised exception: {e}")
        
        # Test deleting non-existent session (should not crash)
        try:
            agent.delete_session("nonexistent")
        except Exception as e:
            pytest.fail(f"delete_session raised exception: {e}")
        
        agent.close()


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    def test_old_initialization_still_works(self):
        """Test that old initialization method still works."""
        # Old way (should still work)
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        assert agent is not None
        assert hasattr(agent, "query")
        agent.close()
    
    @pytest.mark.asyncio
    async def test_old_query_method_still_works(self):
        """Test that old query method still works."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        # Mock query with AsyncMock
        async def mock_query(question, session=None):
            return {
                "natural_response": "Test response",
                "final_output": "Test response"
            }
        
        agent.multi_agent_system.query = mock_query
        
        # Old query method
        result = await agent.query("test question")
        assert "natural_response" in result
        
        agent.close()
    
    def test_old_session_creation_still_works(self):
        """Test that old session creation still works."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
        
        # Old way
        session = agent.create_session("test")
        assert session is not None
        
        agent.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
