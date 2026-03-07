"""
db-query-agent: AI-powered natural language database query system.

A Python package that enables natural language querying of databases using OpenAI Agents SDK.

Quick Start:
    >>> from db_query_agent import DatabaseQueryAgent
    >>> 
    >>> # Option 1: Load from .env
    >>> agent = DatabaseQueryAgent.from_env()
    >>> 
    >>> # Option 2: Pass credentials directly
    >>> agent = DatabaseQueryAgent(
    ...     database_url="postgresql://localhost/mydb",
    ...     openai_api_key="sk-...",
    ...     fast_model="gpt-4o-mini",
    ...     enable_statistics=True
    ... )
    >>> 
    >>> # Query the database
    >>> result = await agent.query("How many users do we have?")
    >>> print(result["natural_response"])
"""

from db_query_agent.agent import DatabaseQueryAgent
from db_query_agent.session_manager import ChatSession
from db_query_agent.config import (
    AgentConfig,
    DatabaseConfig,
    CacheConfig,
    ModelConfig,
    SafetyConfig,
)
from db_query_agent.exceptions import (
    DatabaseQueryAgentError,
    ValidationError,
    QueryExecutionError,
    SchemaExtractionError,
)

__version__ = "0.1.0"
__all__ = [
    # Main agent
    "DatabaseQueryAgent",
    "ChatSession",
    # Configuration classes
    "AgentConfig",
    "DatabaseConfig",
    "CacheConfig",
    "ModelConfig",
    "SafetyConfig",
    # Exceptions
    "DatabaseQueryAgentError",
    "ValidationError",
    "QueryExecutionError",
    "SchemaExtractionError",
]
