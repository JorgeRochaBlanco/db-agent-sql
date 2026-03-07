"""Tests for connection_manager module."""

import pytest
from db_query_agent.connection_manager import ConnectionManager
from db_query_agent.exceptions import QueryExecutionError


class TestConnectionManager:
    """Test ConnectionManager class."""
    
    def test_initialization(self, db_config):
        """Test connection manager initialization."""
        manager = ConnectionManager(db_config)
        assert manager.config == db_config
        assert manager._engine is not None
        manager.close()
    
    def test_engine_property(self, connection_manager):
        """Test engine property."""
        engine = connection_manager.engine
        assert engine is not None
        assert engine.dialect.name == "sqlite"
    
    def test_test_connection(self, connection_manager):
        """Test connection testing."""
        result = connection_manager.test_connection()
        assert result is True
    
    def test_execute_query(self, connection_manager):
        """Test query execution."""
        results = connection_manager.execute_query("SELECT 1 as test")
        assert len(results) == 1
        assert results[0][0] == 1
    
    def test_execute_query_with_results(self, connection_manager):
        """Test query execution with actual data."""
        results = connection_manager.execute_query("SELECT * FROM users")
        assert len(results) == 3  # We inserted 3 users in fixture
    
    @pytest.mark.asyncio
    async def test_execute_query_async(self, connection_manager):
        """Test async query execution."""
        results = await connection_manager.execute_query_async("SELECT 1 as test")
        assert len(results) == 1
        assert results[0][0] == 1
    
    def test_execute_invalid_query(self, connection_manager):
        """Test execution of invalid query."""
        with pytest.raises(QueryExecutionError):
            connection_manager.execute_query("SELECT * FROM nonexistent_table")
    
    def test_get_pool_status(self, connection_manager):
        """Test pool status retrieval."""
        status = connection_manager.get_pool_status()
        assert "size" in status
        assert "checked_in" in status
        assert "checked_out" in status
    
    def test_close(self, db_config):
        """Test connection closing."""
        manager = ConnectionManager(db_config)
        manager.close()
        # After closing, engine should be disposed
        # Creating new connection should work
        manager._engine = None
        engine = manager.engine
        assert engine is not None
        manager.close()
