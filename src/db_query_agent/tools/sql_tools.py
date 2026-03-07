"""Tools for the SQL Query Agent."""

import logging
from typing import Any
from agents import function_tool, RunContextWrapper
from db_query_agent.agent_integration import DatabaseContext

logger = logging.getLogger(__name__)


@function_tool
def get_schema_tool(ctx: RunContextWrapper[DatabaseContext]) -> str:
    """
    Get the complete database schema.
    
    Returns:
        Database schema as formatted string
    """
    try:
        schema = ctx.context.schema_extractor.get_schema()
        formatted = ctx.context.schema_extractor.format_for_llm()
        return formatted
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        return f"Error getting schema: {str(e)}"


@function_tool
def get_relevant_tables_tool(
    ctx: RunContextWrapper[DatabaseContext],
    query: str,
    max_tables: int = 5
) -> str:
    """
    Get relevant tables for a query.
    
    Args:
        query: The user's natural language query
        max_tables: Maximum number of tables to return
        
    Returns:
        Relevant tables with their schema
    """
    try:
        relevant_tables = ctx.context.schema_extractor.get_relevant_tables(
            query,
            max_tables=max_tables
        )
        formatted = ctx.context.schema_extractor.format_for_llm(tables=relevant_tables)
        return formatted
    except Exception as e:
        logger.error(f"Failed to get relevant tables: {e}")
        return f"Error getting relevant tables: {str(e)}"


@function_tool
def validate_query_tool(
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
    try:
        validation = ctx.context.validator.validate(sql)
        
        if validation.is_valid:
            msg = f"✅ Query is valid. Type: {validation.sql_type}"
            if validation.warnings:
                msg += f"\n⚠️ Warnings: {', '.join(validation.warnings)}"
            return msg
        else:
            return f"❌ Query is invalid: {validation.error}"
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return f"Error validating query: {str(e)}"


@function_tool
async def execute_query_tool(
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
        # Validate query first
        validation = ctx.context.validator.validate(sql)
        if not validation.is_valid:
            return f"❌ Validation failed: {validation.error}"
        
        # Execute query
        results = await ctx.context.connection_manager.execute_query_async(
            sql,
            timeout=ctx.context.safety_config.max_query_timeout
        )
        
        # Format results
        if not results:
            return "✅ Query executed successfully. No results returned."
        
        # Limit results
        max_rows = ctx.context.safety_config.max_result_rows
        row_count = len(results)
        
        if row_count > max_rows:
            results = results[:max_rows]
            return f"✅ Query returned {row_count} rows (showing first {max_rows}):\n{results}"
        
        return f"✅ Query returned {row_count} rows:\n{results}"
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return f"❌ Query execution failed: {str(e)}"


@function_tool
def format_results_tool(
    ctx: RunContextWrapper[DatabaseContext],
    results: Any,
    query: str
) -> str:
    """
    Format query results in a natural language response.
    
    Args:
        results: Query results
        query: Original user query
        
    Returns:
        Natural language formatted response
    """
    try:
        if not results:
            return "No results found for your query."
        
        row_count = len(results)
        
        # For single row with single column (like COUNT queries)
        if row_count == 1 and len(results[0]) == 1:
            value = results[0][0]
            
            # Try to get column name
            if hasattr(results[0], '_fields'):
                col_name = results[0]._fields[0]
                
                if 'count' in col_name.lower():
                    if 'user' in query.lower():
                        return f"You have **{value}** users in your database."
                    elif 'order' in query.lower():
                        return f"You have **{value}** orders in your database."
                    elif 'product' in query.lower():
                        return f"You have **{value}** products in your database."
                    else:
                        return f"The count is **{value}**."
                
                elif 'avg' in col_name.lower() or 'average' in col_name.lower():
                    return f"The average value is **{value}**."
                
                elif 'sum' in col_name.lower():
                    return f"The total sum is **{value}**."
                
                elif 'max' in col_name.lower():
                    return f"The maximum value is **{value}**."
                
                elif 'min' in col_name.lower():
                    return f"The minimum value is **{value}**."
                
                else:
                    return f"The **{col_name}** is **{value}**."
            else:
                return f"The result is **{value}**."
        
        # For multiple rows
        elif row_count > 1:
            if row_count <= 5:
                return f"I found **{row_count}** results. Here's what I found."
            else:
                return f"I found **{row_count}** results. You can view them in the details below."
        
        # For single row with multiple columns
        else:
            return f"I found 1 result with multiple fields. Check the details below to see all the information."
            
    except Exception as e:
        logger.error(f"Failed to format results: {e}")
        return "Results retrieved successfully."
