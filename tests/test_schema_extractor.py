"""Tests for schema_extractor module."""

import pytest
import time
from db_query_agent.schema_extractor import SchemaExtractor
from db_query_agent.exceptions import SchemaExtractionError


class TestSchemaExtractor:
    """Test SchemaExtractor class."""
    
    def test_initialization(self, test_engine):
        """Test schema extractor initialization."""
        extractor = SchemaExtractor(test_engine, cache_ttl=60)
        assert extractor.engine == test_engine
        assert extractor.cache_ttl == 60
        assert extractor._schema_cache is None
    
    def test_get_schema(self, schema_extractor):
        """Test schema extraction."""
        schema = schema_extractor.get_schema()
        
        # Check tables exist
        assert "users" in schema
        assert "orders" in schema
        assert "products" in schema
        
        # Check users table structure
        users_table = schema["users"]
        assert users_table["name"] == "users"
        assert len(users_table["columns"]) == 5
        
        # Check columns
        column_names = [col["name"] for col in users_table["columns"]]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "active" in column_names
        assert "created_at" in column_names
    
    def test_schema_caching(self, schema_extractor):
        """Test that schema is cached."""
        # First call - should extract
        schema1 = schema_extractor.get_schema()
        timestamp1 = schema_extractor._cache_timestamp
        
        # Second call - should use cache
        schema2 = schema_extractor.get_schema()
        timestamp2 = schema_extractor._cache_timestamp
        
        assert schema1 == schema2
        assert timestamp1 == timestamp2
    
    def test_force_refresh(self, schema_extractor):
        """Test force refresh of schema."""
        # First call
        schema1 = schema_extractor.get_schema()
        timestamp1 = schema_extractor._cache_timestamp
        
        # Brief pause to ensure timestamp difference
        time.sleep(0.01)
        
        # Force refresh
        schema2 = schema_extractor.get_schema(force_refresh=True)
        timestamp2 = schema_extractor._cache_timestamp
        
        assert schema1 == schema2
        assert timestamp2 > timestamp1
    
    def test_get_relevant_tables(self, schema_extractor):
        """Test relevant table selection."""
        # Query mentioning users
        tables = schema_extractor.get_relevant_tables("show all users")
        assert "users" in tables
        
        # Query mentioning orders
        tables = schema_extractor.get_relevant_tables("count orders")
        assert "orders" in tables
        
        # Query mentioning multiple tables
        tables = schema_extractor.get_relevant_tables("users and their orders")
        assert "users" in tables
        assert "orders" in tables
    
    def test_format_for_llm(self, schema_extractor):
        """Test LLM formatting."""
        formatted = schema_extractor.format_for_llm(tables=["users"])
        
        assert "Database Schema:" in formatted
        assert "Table: users" in formatted
        assert "Columns:" in formatted
        assert "id" in formatted
        assert "name" in formatted
    
    def test_get_dialect(self, schema_extractor):
        """Test dialect detection."""
        dialect = schema_extractor.get_dialect()
        assert dialect == "sqlite"
    
    def test_foreign_keys(self, schema_extractor):
        """Test foreign key extraction."""
        schema = schema_extractor.get_schema()
        orders_table = schema["orders"]
        
        # Check foreign keys
        assert len(orders_table["foreign_keys"]) > 0
        fk = orders_table["foreign_keys"][0]
        assert fk["referred_table"] == "users"
    
    def test_primary_keys(self, schema_extractor):
        """Test primary key extraction."""
        schema = schema_extractor.get_schema()
        users_table = schema["users"]
        
        assert "id" in users_table["primary_keys"]
