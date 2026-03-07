"""Tests for query_validator module."""

import pytest
from db_query_agent.query_validator import QueryValidator, ValidationResult


class TestQueryValidator:
    """Test QueryValidator class."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = QueryValidator(
            read_only=True,
            allowed_tables=["users", "orders"],
            blocked_tables=["admin"],
            max_query_length=5000
        )
        assert validator.read_only is True
        assert validator.allowed_tables == {"users", "orders"}
        assert validator.blocked_tables == {"admin"}
        assert validator.max_query_length == 5000
    
    def test_valid_select_query(self, query_validator):
        """Test validation of valid SELECT query."""
        result = query_validator.validate("SELECT * FROM users")
        assert result.is_valid is True
        assert result.sql_type == "SELECT"
    
    def test_empty_query(self, query_validator):
        """Test validation of empty query."""
        result = query_validator.validate("")
        assert result.is_valid is False
        assert "Empty query" in result.error
    
    def test_query_too_long(self):
        """Test validation of overly long query."""
        validator = QueryValidator(max_query_length=50)
        long_query = "SELECT * FROM users WHERE " + "x" * 100
        result = validator.validate(long_query)
        assert result.is_valid is False
        assert "too long" in result.error
    
    def test_dangerous_keywords_in_readonly(self, query_validator):
        """Test blocking of dangerous keywords in read-only mode."""
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "TRUNCATE TABLE users",
            "ALTER TABLE users ADD COLUMN x",
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET name='test'"
        ]
        
        for query in dangerous_queries:
            result = query_validator.validate(query)
            assert result.is_valid is False
            assert "not allowed" in result.error.lower()
    
    def test_non_select_in_readonly(self, query_validator):
        """Test blocking of non-SELECT queries in read-only mode."""
        result = query_validator.validate("INSERT INTO users VALUES (1, 'test')")
        assert result.is_valid is False
        assert "read-only" in result.error.lower()
    
    def test_blocked_tables(self):
        """Test blocking of specific tables."""
        validator = QueryValidator(
            read_only=True,
            blocked_tables=["admin", "secrets"]
        )
        
        result = validator.validate("SELECT * FROM admin")
        assert result.is_valid is False
        assert "blocked" in result.error.lower()
    
    def test_allowed_tables(self):
        """Test allowlist of tables."""
        validator = QueryValidator(
            read_only=True,
            allowed_tables=["users", "orders"]
        )
        
        # Allowed table
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid is True
        
        # Not in allowlist
        result = validator.validate("SELECT * FROM products")
        assert result.is_valid is False
        assert "not in allowed list" in result.error
    
    def test_select_star_warning(self, query_validator):
        """Test warning for SELECT *."""
        result = query_validator.validate("SELECT * FROM users")
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("SELECT *" in w for w in result.warnings)
    
    def test_sanitize(self, query_validator):
        """Test SQL sanitization."""
        messy_sql = "select   *   from users  where  id=1"
        sanitized = query_validator.sanitize(messy_sql)
        
        assert "SELECT" in sanitized
        assert "FROM" in sanitized
        assert "WHERE" in sanitized
    
    def test_complex_query(self, query_validator):
        """Test validation of complex query."""
        query = """
        SELECT u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.active = 1
        GROUP BY u.name
        HAVING COUNT(o.id) > 5
        ORDER BY order_count DESC
        """
        result = query_validator.validate(query)
        assert result.is_valid is True
        assert result.sql_type == "SELECT"
    
    def test_multiple_statements(self, query_validator):
        """Test validation of multiple statements."""
        query = "SELECT * FROM users; SELECT * FROM orders;"
        result = query_validator.validate(query)
        # Should validate each statement
        assert result.is_valid is True
