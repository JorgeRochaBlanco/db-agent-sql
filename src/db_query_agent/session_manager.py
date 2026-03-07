"""Session management for conversation history using OpenAI Agents SDK."""

import logging
from typing import Optional, Dict, Any
from agents import SQLiteSession
from agents.memory.session import SessionABC

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions using OpenAI Agents SDK sessions."""
    
    def __init__(
        self,
        backend: str = "sqlite",
        db_path: Optional[str] = None
    ):
        """
        Initialize session manager.
        
        Args:
            backend: Session backend ('sqlite' or 'memory')
            db_path: Path to SQLite database file (None = in-memory)
        """
        self.backend = backend
        self.db_path = db_path or ":memory:"
        self._sessions: Dict[str, SessionABC] = {}
    
    def create_session(self, session_id: str) -> SessionABC:
        """
        Create or get a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session instance
        """
        if session_id in self._sessions:
            logger.debug(f"Returning existing session: {session_id}")
            return self._sessions[session_id]
        
        logger.info(f"Creating new session: {session_id}")
        
        if self.backend == "sqlite":
            session = SQLiteSession(session_id, self.db_path)
        else:
            # In-memory session (uses SQLite with :memory:)
            session = SQLiteSession(session_id, ":memory:")
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionABC]:
        """
        Get existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session instance or None if not found
        """
        return self._sessions.get(session_id)
    
    async def clear_session(self, session_id: str) -> None:
        """
        Clear session history.
        
        Args:
            session_id: Session identifier
        """
        session = self.get_session(session_id)
        if session:
            await session.clear_session()
            logger.info(f"Session cleared: {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session deleted: {session_id}")
    
    def list_sessions(self) -> list[str]:
        """
        List all active session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self._sessions.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_sessions": len(self._sessions),
            "backend": self.backend,
            "db_path": self.db_path
        }


class ChatSession:
    """Wrapper for chat-like interface with session."""
    
    def __init__(
        self,
        session_id: str,
        agent: Any,  # DatabaseQueryAgent instance
        session: SessionABC
    ):
        """
        Initialize chat session.
        
        Args:
            session_id: Session identifier
            agent: DatabaseQueryAgent instance (full agent, not just integration)
            session: Session backend
        """
        self.session_id = session_id
        self.agent = agent
        self.session = session
    
    async def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question in the session context with memory.
        
        Args:
            question: User's question
            
        Returns:
            Response dictionary
        """
        logger.info(f"Session {self.session_id} - Question: {question}")
        
        # Use the main agent's query method with session for memory
        result = await self.agent.query(question, session=self.session)
        
        # Session history is handled automatically by OpenAI Agents SDK
        
        return result
    
    async def clear(self) -> None:
        """Clear session history."""
        await self.session.clear_session()
        logger.info(f"Session {self.session_id} cleared")
