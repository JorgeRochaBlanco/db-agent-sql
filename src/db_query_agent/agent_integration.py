"""OpenAI Agents SDK integration for natural language to SQL conversion."""

import logging
from typing import Any, Dict, Optional, AsyncIterator
from pydantic import BaseModel
from agents import Agent, Runner, function_tool, RunContextWrapper, ModelSettings
from db_query_agent.connection_manager import ConnectionManager
from db_query_agent.schema_extractor import SchemaExtractor
from db_query_agent.query_validator import QueryValidator, ValidationResult
from db_query_agent.config import ModelConfig, SafetyConfig

logger = logging.getLogger(__name__)


class QueryResponse(BaseModel):
    """Structured response from the agent."""
    
    sql: str
    explanation: str
    confidence: float = 1.0
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class DatabaseContext:
    """Context passed to agent tools."""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        schema_extractor: SchemaExtractor,
        validator: QueryValidator,
        safety_config: SafetyConfig
    ):
        self.connection_manager = connection_manager
        self.schema_extractor = schema_extractor
        self.validator = validator
        self.safety_config = safety_config


class AgentIntegration:
    """Integrates OpenAI Agents SDK for SQL generation."""
    
    def __init__(
        self,
        context: DatabaseContext,
        model_config: ModelConfig,
        openai_api_key: str
    ):
        """
        Initialize agent integration.
        
        Args:
            context: Database context with tools
            model_config: Model configuration
            openai_api_key: OpenAI API key
        """
        self.context = context
        self.model_config = model_config
        self.openai_api_key = openai_api_key
        self._agent: Optional[Agent] = None
    
    def _create_agent(self, schema_context: str, model_name: str) -> Agent[DatabaseContext]:
        """
        Create OpenAI agent with instructions and tools.
        
        Args:
            schema_context: Formatted schema for context
            model_name: Model to use
            
        Returns:
            Configured agent
        """
        dialect = self.context.schema_extractor.get_dialect()
        
        instructions = f"""You are a database query assistant that converts natural language to SQL.

Database Schema:
{schema_context}

Rules:
- Generate valid {dialect} SQL syntax
- Only generate SELECT queries (read-only mode)
- Use proper JOIN syntax for relationships
- Include appropriate WHERE clauses
- Use meaningful column aliases
- Return queries that are safe and efficient
- If the question is unclear, set needs_clarification=true

Examples:
- "How many users?" -> SELECT COUNT(*) FROM users
- "Show active users" -> SELECT * FROM users WHERE active = true
- "Top 10 products by price" -> SELECT * FROM products ORDER BY price DESC LIMIT 10

Generate the SQL query for the user's question.
"""
        
        agent = Agent[DatabaseContext](
            name="Database Query Agent",
            instructions=instructions,
            model=model_name,
            model_settings=ModelSettings(
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
            ),
            output_type=QueryResponse,
            tools=[
                self._create_execute_query_tool(),
                self._create_validate_query_tool(),
            ]
        )
        
        return agent
    
    def _create_execute_query_tool(self):
        """Create tool for executing SQL queries."""
        
        @function_tool
        async def execute_query(
            ctx: RunContextWrapper[DatabaseContext],
            sql: str
        ) -> str:
            """
            Execute a SQL query and return results.
            
            Args:
                sql: The SQL query to execute
                
            Returns:
                Query results as formatted string
            """
            try:
                # Validate query
                validation = ctx.context.validator.validate(sql)
                if not validation.is_valid:
                    return f"Validation failed: {validation.error}"
                
                # Execute query
                results = await ctx.context.connection_manager.execute_query_async(
                    sql,
                    timeout=ctx.context.safety_config.max_query_timeout
                )
                
                # Format results
                if not results:
                    return "Query executed successfully. No results returned."
                
                # Limit results
                max_rows = ctx.context.safety_config.max_result_rows
                if len(results) > max_rows:
                    results = results[:max_rows]
                    return f"Query returned {len(results)} rows (showing first {max_rows}): {results}"
                
                return f"Query returned {len(results)} rows: {results}"
                
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                return f"Query execution failed: {str(e)}"
        
        return execute_query
    
    def _create_validate_query_tool(self):
        """Create tool for validating SQL queries."""
        
        @function_tool
        def validate_query(
            ctx: RunContextWrapper[DatabaseContext],
            sql: str
        ) -> str:
            """
            Validate a SQL query without executing it.
            
            Args:
                sql: The SQL query to validate
                
            Returns:
                Validation result
            """
            validation = ctx.context.validator.validate(sql)
            
            if validation.is_valid:
                msg = f"Query is valid. Type: {validation.sql_type}"
                if validation.warnings:
                    msg += f"\nWarnings: {', '.join(validation.warnings)}"
                return msg
            else:
                return f"Query is invalid: {validation.error}"
        
        return validate_query
    
    def _select_model(self, query: str) -> str:
        """
        Select appropriate model based on query complexity.
        
        Args:
            query: User's natural language query
            
        Returns:
            Model name to use
        """
        if self.model_config.strategy != "adaptive":
            return self.model_config.balanced_model
        
        # Simple query indicators
        simple_patterns = [
            "how many", "count", "total", "sum",
            "show all", "list all", "get all",
            "find", "select"
        ]
        
        # Complex query indicators
        complex_patterns = [
            "compare", "between", "group by", "having",
            "join", "relationship", "correlation",
            "average by", "breakdown", "analysis"
        ]
        
        query_lower = query.lower()
        
        # Check for complex patterns
        if any(pattern in query_lower for pattern in complex_patterns):
            logger.debug(f"Using complex model for query: {query[:50]}...")
            return self.model_config.complex_model
        
        # Check for simple patterns
        if any(pattern in query_lower for pattern in simple_patterns):
            logger.debug(f"Using fast model for query: {query[:50]}...")
            return self.model_config.fast_model
        
        # Default to balanced
        logger.debug(f"Using balanced model for query: {query[:50]}...")
        return self.model_config.balanced_model
    
    async def generate_sql(
        self,
        question: str,
        max_tables: Optional[int] = None,
        session: Optional[Any] = None
    ) -> QueryResponse:
        """
        Generate SQL from natural language query.
        
        Args:
            question: User's natural language question
            max_tables: Maximum tables to include in context
            session: Optional session for conversation history
            
        Returns:
            QueryResponse with SQL and metadata
        """
        logger.info(f"Generating SQL for query: {question}")
        
        # Get relevant schema
        relevant_tables = self.context.schema_extractor.get_relevant_tables(
            question,
            max_tables=max_tables
        )
        schema_context = self.context.schema_extractor.format_for_llm(
            tables=relevant_tables
        )
        
        # Select model
        model_name = self._select_model(question)
        
        # Create agent
        agent = self._create_agent(schema_context, model_name)
        
        # Run agent with optional session for memory
        result = await Runner.run(
            agent,
            input=question,
            context=self.context,
            session=session  # Pass session for conversation history
        )
        
        return result.final_output
    
    async def generate_sql_stream(
        self,
        user_query: str,
        max_tables: int = 5
    ) -> AsyncIterator[str]:
        """
        Generate SQL with streaming responses.
        
        Args:
            user_query: User's natural language question
            max_tables: Maximum tables to include in context
            
        Yields:
            Tokens as they are generated
        """
        logger.info(f"Generating SQL (streaming) for query: {user_query}")
        
        # Get relevant schema
        relevant_tables = self.context.schema_extractor.get_relevant_tables(
            user_query,
            max_tables=max_tables
        )
        schema_context = self.context.schema_extractor.format_for_llm(
            tables=relevant_tables
        )
        
        # Select model
        model_name = self._select_model(user_query)
        
        # Create agent
        agent = self._create_agent(schema_context, model_name)
        
        # Run agent with streaming
        result = Runner.run_streamed(
            agent,
            input=user_query,
            context=self.context
        )
        
        # Stream events
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                # Stream text deltas
                if hasattr(event.data, 'delta'):
                    yield event.data.delta
