"""Tests for streaming functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from db_query_agent import DatabaseQueryAgent
from db_query_agent.simple_multi_agent_system import SimpleMultiAgentSystem


class TestStreamingFunctionality:
    """Test streaming query functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with streaming enabled."""
        return DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True,
            enable_statistics=True
        )
    
    @pytest.mark.asyncio
    async def test_query_stream_returns_async_iterator(self, agent):
        """Test that query_stream returns an async iterator."""
        # Mock the multi_agent_system.query_stream
        async def mock_stream(question, session=None):
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk
        
        agent.multi_agent_system.query_stream = mock_stream
        
        # Collect streamed chunks
        chunks = []
        async for chunk in agent.query_stream("test question"):
            chunks.append(chunk)
        
        assert chunks == ["Hello", " ", "world", "!"]
        assert "".join(chunks) == "Hello world!"
    
    @pytest.mark.asyncio
    async def test_query_stream_with_session(self, agent):
        """Test streaming with session context."""
        # Create a session
        session = agent.create_session("test_session")
        
        # Mock the multi_agent_system.query_stream
        async def mock_stream(question, session=None):
            assert session is not None
            yield "Response with session"
        
        agent.multi_agent_system.query_stream = mock_stream
        
        # Stream with session
        chunks = []
        async for chunk in agent.query_stream("test", session=session.session):
            chunks.append(chunk)
        
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_query_stream_error_handling(self, agent):
        """Test error handling in streaming."""
        # Mock to raise an error
        async def mock_stream_error(question, session=None):
            raise Exception("Streaming error")
            yield  # Never reached
        
        agent.multi_agent_system.query_stream = mock_stream_error
        
        # Should yield error message
        chunks = []
        async for chunk in agent.query_stream("test"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert "error" in "".join(chunks).lower()


class TestMultiAgentStreamig:
    """Test multi-agent system streaming."""
    
    @pytest.fixture
    def mock_db_context(self):
        """Create mock database context."""
        context = MagicMock()
        context.connection_manager.engine.dialect.name = "sqlite"
        context.schema_extractor.get_dialect.return_value = "sqlite"
        context.schema_extractor.get_schema.return_value = {}
        return context
    
    @pytest.fixture
    def mock_model_config(self):
        """Create mock model config."""
        from db_query_agent.config import ModelConfig
        return ModelConfig(
            strategy="adaptive",
            fast_model="gpt-4o-mini",
            balanced_model="gpt-4.1-mini",
            complex_model="gpt-4.1"
        )
    
    @pytest.mark.asyncio
    async def test_multi_agent_query_stream(self, mock_db_context, mock_model_config):
        """Test multi-agent system query_stream method."""
        system = SimpleMultiAgentSystem(
            database_context=mock_db_context,
            model_config=mock_model_config,
            openai_api_key="sk-test-key",
            cache_enabled=False
        )
        
        # Mock Runner.run_streamed
        with patch("db_query_agent.simple_multi_agent_system.Runner") as mock_runner:
            # Create mock stream events
            async def mock_stream_events():
                from openai.types.responses import ResponseTextDeltaEvent
                
                # Mock text delta events
                for text in ["Hello", " ", "world"]:
                    event = MagicMock()
                    event.type = "raw_response_event"
                    event.data = MagicMock(spec=ResponseTextDeltaEvent)
                    event.data.delta = text
                    yield event
            
            mock_result = MagicMock()
            mock_result.stream_events = mock_stream_events
            mock_runner.run_streamed.return_value = mock_result
            
            # Test streaming
            chunks = []
            async for chunk in system.query_stream("test question"):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " ", "world"]
    
    @pytest.mark.asyncio
    async def test_streaming_with_cache_hit(self, mock_db_context, mock_model_config):
        """Test that cached responses are returned instantly."""
        # Create mock cache manager
        mock_cache = MagicMock()
        mock_cache.get_llm_response.return_value = {
            "natural_response": "Cached response",
            "final_output": "Cached response"
        }
        
        system = SimpleMultiAgentSystem(
            database_context=mock_db_context,
            model_config=mock_model_config,
            openai_api_key="sk-test-key",
            cache_manager=mock_cache,
            cache_enabled=True
        )
        
        # Test streaming with cache hit
        chunks = []
        async for chunk in system.query_stream("test question"):
            chunks.append(chunk)
        
        # Should return cached response
        assert "".join(chunks) == "Cached response"
        mock_cache.get_llm_response.assert_called_once()


class TestStreamingIntegration:
    """Integration tests for streaming."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_streaming(self):
        """Test end-to-end streaming flow."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True
        )
        
        # Mock the streaming response
        async def mock_stream(question, session=None):
            response = "You have 10 users in your database."
            for char in response:
                yield char
        
        agent.multi_agent_system.query_stream = mock_stream
        
        # Collect full response
        full_response = ""
        async for chunk in agent.query_stream("How many users?"):
            full_response += chunk
        
        assert full_response == "You have 10 users in your database."
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self):
        """Test that streaming starts quickly."""
        import time
        
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True
        )
        
        # Mock fast streaming
        async def mock_fast_stream(question, session=None):
            yield "First"
            await asyncio.sleep(0.01)
            yield " chunk"
        
        agent.multi_agent_system.query_stream = mock_fast_stream
        
        start_time = time.time()
        first_chunk_time = None
        
        async for chunk in agent.query_stream("test"):
            if first_chunk_time is None:
                first_chunk_time = time.time()
            break
        
        # First chunk should arrive quickly (< 100ms)
        time_to_first_chunk = first_chunk_time - start_time
        assert time_to_first_chunk < 0.1


class TestStreamingConfiguration:
    """Test streaming configuration options."""
    
    def test_streaming_disabled_uses_regular_query(self):
        """Test that disabled streaming uses regular query."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=False
        )
        
        assert agent.enable_streaming is False
        assert hasattr(agent, "query_stream")  # Method still exists
    
    def test_streaming_enabled_flag(self):
        """Test streaming enabled flag."""
        agent = DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key",
            enable_streaming=True
        )
        
        assert agent.enable_streaming is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
