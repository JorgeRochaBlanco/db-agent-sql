"""Tests for session_manager module."""

import pytest
from db_query_agent.session_manager import SessionManager, ChatSession


class TestSessionManager:
    """Test SessionManager class."""
    
    def test_initialization(self):
        """Test session manager initialization."""
        manager = SessionManager(backend="sqlite", db_path=":memory:")
        assert manager.backend == "sqlite"
        assert manager.db_path == ":memory:"
        assert len(manager._sessions) == 0
    
    def test_create_session(self):
        """Test session creation."""
        manager = SessionManager()
        session = manager.create_session("test_session_1")
        
        assert session is not None
        assert "test_session_1" in manager._sessions
    
    def test_create_duplicate_session(self):
        """Test creating duplicate session returns existing."""
        manager = SessionManager()
        session1 = manager.create_session("test_session_1")
        session2 = manager.create_session("test_session_1")
        
        assert session1 == session2
    
    def test_get_session(self):
        """Test getting existing session."""
        manager = SessionManager()
        created = manager.create_session("test_session_1")
        retrieved = manager.get_session("test_session_1")
        
        assert created == retrieved
    
    def test_get_nonexistent_session(self):
        """Test getting non-existent session."""
        manager = SessionManager()
        session = manager.get_session("nonexistent")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_clear_session(self):
        """Test clearing session history."""
        manager = SessionManager()
        session = manager.create_session("test_session_1")
        
        await manager.clear_session("test_session_1")
        # Session should still exist but be empty
        assert manager.get_session("test_session_1") is not None
    
    def test_delete_session(self):
        """Test deleting session."""
        manager = SessionManager()
        manager.create_session("test_session_1")
        
        assert "test_session_1" in manager._sessions
        
        manager.delete_session("test_session_1")
        assert "test_session_1" not in manager._sessions
    
    def test_list_sessions(self):
        """Test listing all sessions."""
        manager = SessionManager()
        manager.create_session("session_1")
        manager.create_session("session_2")
        manager.create_session("session_3")
        
        sessions = manager.list_sessions()
        assert len(sessions) == 3
        assert "session_1" in sessions
        assert "session_2" in sessions
        assert "session_3" in sessions
    
    def test_get_stats(self):
        """Test getting session statistics."""
        manager = SessionManager()
        manager.create_session("session_1")
        manager.create_session("session_2")
        
        stats = manager.get_stats()
        assert stats["total_sessions"] == 2
        assert stats["backend"] == "sqlite"


class TestChatSession:
    """Test ChatSession class."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        from unittest.mock import Mock, AsyncMock
        
        mock = Mock()
        # Mock the query method to return async
        async def mock_query(question, session=None):
            return {
                "natural_response": "Test response",
                "final_output": "Test response"
            }
        mock.query = mock_query
        return mock
    
    @pytest.fixture
    def chat_session(self, mock_agent):
        """Create chat session for testing."""
        manager = SessionManager()
        session = manager.create_session("test_chat")
        return ChatSession("test_chat", mock_agent, session)
    
    def test_initialization(self, chat_session, mock_agent):
        """Test chat session initialization."""
        assert chat_session.session_id == "test_chat"
        assert chat_session.agent == mock_agent
        assert chat_session.session is not None
    
    @pytest.mark.asyncio
    async def test_ask(self, chat_session):
        """Test asking a question."""
        response = await chat_session.ask("show all users")
        
        assert "natural_response" in response
        assert response["natural_response"] == "Test response"
    
    @pytest.mark.asyncio
    async def test_clear(self, chat_session):
        """Test clearing chat session."""
        await chat_session.clear()
        # Should not raise an error
