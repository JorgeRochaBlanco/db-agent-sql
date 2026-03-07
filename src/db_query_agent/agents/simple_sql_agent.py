"""Simple SQL Agent - Backend worker for SQL generation and execution."""

import logging
from pydantic import BaseModel
from typing import Optional, List, Any
from agents import Agent, ModelSettings
from db_query_agent.tools.sql_tools import (
    get_schema_tool,
    get_relevant_tables_tool,
    validate_query_tool,
    execute_query_tool,
)
from db_query_agent.agent_integration import DatabaseContext

logger = logging.getLogger(__name__)


class SQLQueryResult(BaseModel):
    """Structured output from SQL Agent."""
    sql: str
    success: bool
    row_count: int = 0
    results: Optional[str] = None  # JSON string of results
    error: Optional[str] = None


class SimpleSQLAgent:
    """Simple SQL Agent - generates and executes SQL queries."""
    
    @staticmethod
    def create(model: str = "gpt-4o-mini", dialect: str = "sqlite") -> Agent[DatabaseContext]:
        """
        Create a simple SQL Agent that returns structured results.
        
        Args:
            model: Model to use
            dialect: SQL dialect
            
        Returns:
            Configured SQL agent
        """
        instructions = f"""You are a SQL query agent. Generate and execute SQL queries from natural language.

**Your job:**
1. Understand the natural language query
2. Use get_relevant_tables_tool to get schema
3. Generate valid {dialect} SQL
4. Use validate_query_tool to check safety
5. Use execute_query_tool to run the query
6. Return structured results

**Rules:**
- Only generate SELECT queries (read-only)
- Use proper {dialect} syntax
- Include appropriate WHERE clauses
- Use LIMIT for large result sets
- Handle errors gracefully

**Workflow:**
1. get_relevant_tables_tool("user query")
2. Generate SQL based on schema
3. validate_query_tool(sql)
4. execute_query_tool(sql)
5. Return results

**Examples:**

Input: "How many users do we have?"
1. get_relevant_tables_tool("users count")
2. SQL: SELECT COUNT(*) AS total_users FROM users
3. validate_query_tool(sql) ✓
4. execute_query_tool(sql) → [(150,)]
5. Return: {{"sql": "SELECT...", "success": true, "row_count": 1, "results": "150"}}

Input: "Show me active users"
1. get_relevant_tables_tool("users active")
2. SQL: SELECT * FROM users WHERE active = true LIMIT 10
3. validate_query_tool(sql) ✓
4. execute_query_tool(sql) → [10 rows]
5. Return: {{"sql": "SELECT...", "success": true, "row_count": 10, "results": "10 users found"}}

**Important:** Return ONLY structured data. No conversational text!
"""
        
        agent = Agent[DatabaseContext](
            name="SQL Query Agent",
            instructions=instructions,
            model=model,
            model_settings=ModelSettings(
                temperature=0.0,  # Deterministic SQL generation
            ),
            tools=[
                get_relevant_tables_tool,
                validate_query_tool,
                execute_query_tool,
            ],
            output_type=SQLQueryResult,  # Structured output
        )
        
        logger.info("Simple SQL Agent created")
        return agent
