"""Pytest configuration and fixtures."""

import pytest
import os
from sqlalchemy import create_engine, text
from db_query_agent.config import DatabaseConfig, CacheConfig, ModelConfig, SafetyConfig
from db_query_agent.connection_manager import ConnectionManager
from db_query_agent.schema_extractor import SchemaExtractor
from db_query_agent.cache_manager import CacheManager
from db_query_agent.query_validator import QueryValidator


@pytest.fixture
def test_database_url():
    """Test database URL (SQLite in-memory)."""
    return "sqlite:///:memory:"


@pytest.fixture
def test_engine(test_database_url):
    """Create test database engine."""
    engine = create_engine(test_database_url)
    
    # Create test tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total REAL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                category TEXT
            )
        """))
        
        # Insert test data
        conn.execute(text("""
            INSERT INTO users (id, name, email, active) VALUES
            (1, 'Alice', 'alice@example.com', 1),
            (2, 'Bob', 'bob@example.com', 1),
            (3, 'Charlie', 'charlie@example.com', 0)
        """))
        
        conn.execute(text("""
            INSERT INTO orders (id, user_id, total, status) VALUES
            (1, 1, 99.99, 'completed'),
            (2, 1, 149.99, 'completed'),
            (3, 2, 79.99, 'pending')
        """))
        
        conn.execute(text("""
            INSERT INTO products (id, name, price, category) VALUES
            (1, 'Laptop', 999.99, 'electronics'),
            (2, 'Mouse', 29.99, 'electronics'),
            (3, 'Desk', 299.99, 'furniture')
        """))
        
        conn.commit()
    
    yield engine
    engine.dispose()


@pytest.fixture
def db_config(test_database_url):
    """Database configuration for testing."""
    return DatabaseConfig(
        url=test_database_url,
        pool_size=5,
        max_overflow=10
    )


@pytest.fixture
def cache_config():
    """Cache configuration for testing."""
    return CacheConfig(
        enabled=True,
        backend="memory",
        schema_ttl=60,
        query_ttl=30,
        llm_ttl=60
    )


@pytest.fixture
def model_config():
    """Model configuration for testing."""
    return ModelConfig(
        strategy="adaptive",
        fast_model="gpt-4o-mini",
        balanced_model="gpt-4.1-mini",
        complex_model="gpt-4.1"
    )


@pytest.fixture
def safety_config():
    """Safety configuration for testing."""
    return SafetyConfig(
        read_only=True,
        allowed_tables=None,
        blocked_tables=None,
        max_query_timeout=30,
        max_result_rows=1000
    )


@pytest.fixture
def connection_manager(test_engine):
    """Connection manager instance."""
    # Create a config using the test engine's URL
    db_config = DatabaseConfig(
        url=str(test_engine.url),
        pool_size=5,
        max_overflow=10
    )
    # Create manager but use the existing test_engine
    manager = ConnectionManager(db_config)
    # Replace the engine with our test_engine that has data
    manager._engine = test_engine
    yield manager
    # Don't close test_engine here as it's managed by test_engine fixture


@pytest.fixture
def schema_extractor(test_engine):
    """Schema extractor instance."""
    return SchemaExtractor(test_engine, cache_ttl=60)


@pytest.fixture
def cache_manager():
    """Cache manager instance."""
    return CacheManager(schema_ttl=60, query_ttl=30, llm_ttl=60)


@pytest.fixture
def query_validator():
    """Query validator instance."""
    return QueryValidator(
        read_only=True,
        allowed_tables=None,
        blocked_tables=None
    )
