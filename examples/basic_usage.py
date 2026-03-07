"""
Basic usage examples for db-query-agent.

This file demonstrates the most common use cases.
"""

import asyncio
from db_query_agent import DatabaseQueryAgent


async def example_1_simple_query():
    """Example 1: Simple query with direct configuration."""
    print("\n" + "="*60)
    print("Example 1: Simple Query")
    print("="*60)
    
    # Create agent with direct configuration
    agent = DatabaseQueryAgent(
        database_url="sqlite:///demo_database.db",
        openai_api_key="your-api-key-here",
        enable_statistics=True
    )
    
    # Ask a question
    result = await agent.query("How many users do we have?")
    
    # Print response
    print(f"\nQuestion: {result['question']}")
    print(f"Answer: {result['natural_response']}")
    
    if result.get('sql'):
        print(f"SQL: {result['sql']}")
    
    # Cleanup
    agent.close()


async def example_2_env_configuration():
    """Example 2: Load configuration from .env file."""
    print("\n" + "="*60)
    print("Example 2: Configuration from .env")
    print("="*60)
    
    # Load from .env file
    agent = DatabaseQueryAgent.from_env(
        enable_statistics=True
    )
    
    # Ask multiple questions
    questions = [
        "How many users do we have?",
        "Show me the top 5 products by price",
        "What's the total revenue?"
    ]
    
    for question in questions:
        result = await agent.query(question)
        print(f"\nQ: {question}")
        print(f"A: {result['natural_response']}")
    
    # Get statistics
    stats = agent.get_stats()
    print(f"\n📊 Statistics:")
    print(f"Total queries: {stats['total_queries']}")
    print(f"Cache hits: {stats['cache_hits']}")
    
    agent.close()


async def example_3_streaming():
    """Example 3: Streaming responses."""
    print("\n" + "="*60)
    print("Example 3: Streaming Responses")
    print("="*60)
    
    # Enable streaming
    agent = DatabaseQueryAgent.from_env(
        enable_streaming=True
    )
    
    # Stream response
    print("\nQuestion: How many orders do we have?")
    print("Answer: ", end="", flush=True)
    
    async for chunk in agent.query_stream("How many orders do we have?"):
        print(chunk, end="", flush=True)
    
    print()  # New line
    
    agent.close()


async def example_4_sessions():
    """Example 4: Session-based conversations."""
    print("\n" + "="*60)
    print("Example 4: Session-based Conversations")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env()
    
    # Create a session
    session = agent.create_session("user_123")
    
    # Multi-turn conversation
    questions = [
        "How many users do we have?",
        "Show me the active ones",
        "Filter by users created this month"
    ]
    
    for question in questions:
        result = await session.ask(question)
        print(f"\nQ: {question}")
        print(f"A: {result['natural_response']}")
    
    # List sessions
    sessions = agent.list_sessions()
    print(f"\n📋 Active sessions: {sessions}")
    
    # Cleanup
    agent.delete_session("user_123")
    agent.close()


async def example_5_schema_exploration():
    """Example 5: Explore database schema."""
    print("\n" + "="*60)
    print("Example 5: Schema Exploration")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env()
    
    # Get schema info
    schema_info = agent.get_schema_info(include_foreign_keys=True)
    
    print(f"\n📚 Database Schema:")
    print(f"Total tables: {schema_info['total_tables']}")
    print(f"Relationships: {len(schema_info['relationships'])}")
    
    # Show tables
    print("\nTables:")
    for table_name, table_info in schema_info['tables'].items():
        print(f"\n  {table_name}:")
        print(f"    Columns: {len(table_info['columns'])}")
        print(f"    Primary Keys: {table_info['primary_keys']}")
        
        if table_info['foreign_keys']:
            print(f"    Foreign Keys: {len(table_info['foreign_keys'])}")
    
    # Show relationships
    if schema_info['relationships']:
        print("\nRelationships:")
        for rel in schema_info['relationships'][:5]:  # Show first 5
            print(f"  {rel['from_table']}.{rel['from_columns']} → "
                  f"{rel['to_table']}.{rel['to_columns']}")
    
    agent.close()


async def example_6_error_handling():
    """Example 6: Error handling."""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(read_only=True)
    
    # Try an invalid query
    try:
        result = await agent.query("DROP TABLE users")
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    # Try a valid query
    try:
        result = await agent.query("How many users?")
        print(f"\n✅ Success: {result['natural_response']}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    agent.close()


async def example_7_custom_configuration():
    """Example 7: Custom configuration."""
    print("\n" + "="*60)
    print("Example 7: Custom Configuration")
    print("="*60)
    
    # Custom configuration
    agent = DatabaseQueryAgent(
        database_url="sqlite:///demo_database.db",
        openai_api_key="your-api-key-here",
        # Model configuration
        model_strategy="adaptive",
        fast_model="gpt-4o-mini",
        complex_model="gpt-4.1",
        # Cache configuration
        enable_cache=True,
        cache_backend="memory",
        schema_cache_ttl=3600,
        # Safety configuration
        read_only=True,
        max_query_timeout=30,
        max_result_rows=1000,
        # Performance configuration
        pool_size=10,
        lazy_schema_loading=True,
        # Features
        enable_statistics=True,
        enable_streaming=False
    )
    
    result = await agent.query("Show me some data")
    print(f"\nAnswer: {result['natural_response']}")
    
    # Show configuration
    print(f"\n⚙️ Configuration:")
    print(f"Model strategy: {agent.config.model.strategy}")
    print(f"Cache enabled: {agent.config.cache.enabled}")
    print(f"Read-only: {agent.config.safety.read_only}")
    print(f"Statistics enabled: {agent.enable_statistics}")
    
    agent.close()


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("DB Query Agent - Basic Usage Examples")
    print("="*60)
    
    # Run examples
    await example_1_simple_query()
    await example_2_env_configuration()
    await example_3_streaming()
    await example_4_sessions()
    await example_5_schema_exploration()
    await example_6_error_handling()
    await example_7_custom_configuration()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
