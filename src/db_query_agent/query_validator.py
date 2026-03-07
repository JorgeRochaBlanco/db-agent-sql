"""SQL query validation and safety checks."""

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML
from typing import List, Optional
from pydantic import BaseModel
from db_query_agent.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of query validation."""
    
    is_valid: bool
    error: Optional[str] = None
    warnings: List[str] = []
    sql_type: Optional[str] = None


class QueryValidator:
    """Validates and sanitizes SQL queries."""
    
    # Dangerous SQL keywords that should be blocked in read-only mode
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC",
        "EXECUTE", "CALL", "MERGE"
    }
    
    def __init__(
        self,
        read_only: bool = True,
        allowed_tables: Optional[List[str]] = None,
        blocked_tables: Optional[List[str]] = None,
        max_query_length: int = 10000
    ):
        """
        Initialize query validator.
        
        Args:
            read_only: Only allow SELECT queries
            allowed_tables: List of allowed tables (None = all)
            blocked_tables: List of blocked tables
            max_query_length: Maximum query length in characters
        """
        self.read_only = read_only
        self.allowed_tables = set(allowed_tables) if allowed_tables else None
        self.blocked_tables = set(blocked_tables) if blocked_tables else set()
        self.max_query_length = max_query_length
    
    def validate(self, sql: str) -> ValidationResult:
        """
        Validate SQL query.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            ValidationResult with validation status
        """
        warnings = []
        
        # Check length
        if len(sql) > self.max_query_length:
            return ValidationResult(
                is_valid=False,
                error=f"Query too long: {len(sql)} characters (max: {self.max_query_length})"
            )
        
        # Check if empty
        if not sql.strip():
            return ValidationResult(
                is_valid=False,
                error="Empty query"
            )
        
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql)
            
            if not parsed:
                return ValidationResult(
                    is_valid=False,
                    error="Failed to parse SQL"
                )
            
            # Check each statement
            for statement in parsed:
                result = self._validate_statement(statement)
                if not result.is_valid:
                    return result
                warnings.extend(result.warnings)
            
            # Get SQL type
            sql_type = self._get_sql_type(parsed[0])
            
            return ValidationResult(
                is_valid=True,
                warnings=warnings,
                sql_type=sql_type
            )
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error=f"Validation failed: {str(e)}"
            )
    
    def _validate_statement(self, statement: Statement) -> ValidationResult:
        """Validate a single SQL statement."""
        warnings = []
        
        # Get statement type
        sql_type = self._get_sql_type(statement)
        
        # Check for dangerous keywords in read-only mode
        if self.read_only:
            sql_upper = str(statement).upper()
            for keyword in self.DANGEROUS_KEYWORDS:
                if keyword in sql_upper:
                    return ValidationResult(
                        is_valid=False,
                        error=f"Dangerous keyword '{keyword}' not allowed in read-only mode"
                    )
            
            # Only allow SELECT
            if sql_type and sql_type != "SELECT":
                return ValidationResult(
                    is_valid=False,
                    error=f"Only SELECT queries allowed in read-only mode, got: {sql_type}"
                )
        
        # Check for blocked tables
        tables = self._extract_tables(statement)
        for table in tables:
            if table in self.blocked_tables:
                return ValidationResult(
                    is_valid=False,
                    error=f"Access to table '{table}' is blocked"
                )
            
            # Check allowed tables
            if self.allowed_tables and table not in self.allowed_tables:
                return ValidationResult(
                    is_valid=False,
                    error=f"Table '{table}' is not in allowed list"
                )
        
        # Check for SELECT *
        if "SELECT *" in str(statement).upper():
            warnings.append("Using SELECT * may return unnecessary data")
        
        return ValidationResult(
            is_valid=True,
            warnings=warnings,
            sql_type=sql_type
        )
    
    def _get_sql_type(self, statement: Statement) -> Optional[str]:
        """Get SQL statement type (SELECT, INSERT, etc.)."""
        for token in statement.tokens:
            if token.ttype is DML:
                return token.value.upper()
        return None
    
    def _extract_tables(self, statement: Statement) -> List[str]:
        """Extract table names from SQL statement."""
        tables = []
        
        # Simple extraction - look for FROM and JOIN clauses
        sql_str = str(statement).upper()
        
        # This is a simplified approach
        # In production, you'd want more robust parsing
        tokens = sql_str.split()
        for i, token in enumerate(tokens):
            if token in ("FROM", "JOIN") and i + 1 < len(tokens):
                table_name = tokens[i + 1].strip("(),;").lower()
                if table_name and not table_name.startswith("("):
                    tables.append(table_name)
        
        return tables
    
    def sanitize(self, sql: str) -> str:
        """
        Sanitize SQL query.
        
        Args:
            sql: SQL query to sanitize
            
        Returns:
            Sanitized SQL
        """
        # Parse and format
        formatted = sqlparse.format(
            sql,
            reindent=True,
            keyword_case="upper",
            strip_comments=True
        )
        
        return formatted.strip()
