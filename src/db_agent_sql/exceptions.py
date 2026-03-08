"""Custom exceptions for db-query-agent."""


class DatabaseQueryAgentError(Exception):
    """Base exception for all db-query-agent errors."""
    pass


class ValidationError(DatabaseQueryAgentError):
    """Raised when query validation fails."""
    pass


class QueryExecutionError(DatabaseQueryAgentError):
    """Raised when query execution fails."""
    pass


class SchemaExtractionError(DatabaseQueryAgentError):
    """Raised when schema extraction fails."""
    pass


class CacheError(DatabaseQueryAgentError):
    """Raised when cache operations fail."""
    pass


class ConnectionError(DatabaseQueryAgentError):
    """Raised when database connection fails."""
    pass
