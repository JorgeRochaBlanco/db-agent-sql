"""
Advanced usage examples for db-query-agent.

This file demonstrates advanced features and patterns.
"""

import asyncio
from db_query_agent import DatabaseQueryAgent
from typing import List, Dict, Any
import time


async def example_1_batch_queries():
    """Example 1: Execute multiple queries efficiently."""
    print("\n" + "="*60)
    print("Example 1: Batch Queries")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(enable_statistics=True)
    
    questions = [
        "How many users do we have?",
        "What's the total number of orders?",
        "Show me the top 5 products",
        "What's the average order value?",
        "How many active users?"
    ]
    
    # Execute all queries
    results = []
    start_time = time.time()
    
    for question in questions:
        result = await agent.query(question)
        results.append(result)
        print(f"\nQ: {question}")
        print(f"A: {result['natural_response']}")
    
    # Show performance
    total_time = time.time() - start_time
    stats = agent.get_stats()
    
    print(f"\n📊 Performance:")
    print(f"Total queries: {len(questions)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time: {total_time/len(questions):.2f}s per query")
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Cache hit rate: {(stats['cache_hits']/stats['total_queries']*100):.1f}%")
    
    agent.close()


async def example_2_concurrent_queries():
    """Example 2: Execute queries concurrently."""
    print("\n" + "="*60)
    print("Example 2: Concurrent Queries")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(
        pool_size=20,  # Increase pool for concurrency
        enable_statistics=True
    )
    
    questions = [
        "How many users?",
        "How many orders?",
        "How many products?",
        "Total revenue?",
        "Active users count?"
    ]
    
    # Execute concurrently
    start_time = time.time()
    
    tasks = [agent.query(q) for q in questions]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Show results
    for question, result in zip(questions, results):
        print(f"\nQ: {question}")
        print(f"A: {result['natural_response']}")
    
    print(f"\n⚡ Concurrent execution time: {total_time:.2f}s")
    print(f"Average: {total_time/len(questions):.2f}s per query")
    
    agent.close()


async def example_3_streaming_with_processing():
    """Example 3: Process streaming responses."""
    print("\n" + "="*60)
    print("Example 3: Streaming with Processing")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(enable_streaming=True)
    
    # Stream and process
    full_response = ""
    word_count = 0
    
    print("\nQuestion: Explain the database schema")
    print("Answer: ", end="", flush=True)
    
    async for chunk in agent.query_stream("Explain the database schema"):
        print(chunk, end="", flush=True)
        full_response += chunk
        if chunk == " ":
            word_count += 1
    
    print(f"\n\n📝 Response stats:")
    print(f"Total characters: {len(full_response)}")
    print(f"Approximate words: {word_count}")
    
    agent.close()


async def example_4_session_management():
    """Example 4: Advanced session management."""
    print("\n" + "="*60)
    print("Example 4: Advanced Session Management")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env()
    
    # Create multiple sessions
    sessions = {}
    for i in range(3):
        session_id = f"user_{i+1}"
        sessions[session_id] = agent.create_session(session_id)
    
    # Use sessions
    for session_id, session in sessions.items():
        result = await session.ask(f"Hello, I'm {session_id}")
        print(f"\n{session_id}: {result['natural_response']}")
    
    # List all sessions
    all_sessions = agent.list_sessions()
    print(f"\n📋 Active sessions: {all_sessions}")
    
    # Clear one session
    agent.clear_session("user_1")
    print(f"Cleared session: user_1")
    
    # Delete sessions
    for session_id in sessions.keys():
        agent.delete_session(session_id)
    
    print(f"Deleted all sessions")
    print(f"Remaining sessions: {agent.list_sessions()}")
    
    agent.close()


async def example_5_caching_strategies():
    """Example 5: Demonstrate caching benefits."""
    print("\n" + "="*60)
    print("Example 5: Caching Strategies")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(
        enable_cache=True,
        enable_statistics=True
    )
    
    question = "How many users do we have?"
    
    # First query (cache miss)
    print("\n1st query (cache miss):")
    start = time.time()
    result1 = await agent.query(question)
    time1 = time.time() - start
    print(f"Answer: {result1['natural_response']}")
    print(f"Time: {time1:.3f}s")
    
    # Second query (cache hit)
    print("\n2nd query (cache hit):")
    start = time.time()
    result2 = await agent.query(question)
    time2 = time.time() - start
    print(f"Answer: {result2['natural_response']}")
    print(f"Time: {time2:.3f}s")
    
    # Show improvement
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"\n⚡ Speedup: {speedup:.1f}x faster")
    
    # Show cache stats
    stats = agent.get_stats()
    print(f"\n📊 Cache stats:")
    print(f"Total queries: {stats['total_queries']}")
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Hit rate: {(stats['cache_hits']/stats['total_queries']*100):.1f}%")
    
    agent.close()


async def example_6_error_recovery():
    """Example 6: Error handling and recovery."""
    print("\n" + "="*60)
    print("Example 6: Error Recovery")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(
        read_only=True,
        enable_statistics=True
    )
    
    # Try invalid queries with recovery
    queries = [
        ("DROP TABLE users", "How many users?"),  # Invalid, then valid
        ("DELETE FROM orders", "How many orders?"),  # Invalid, then valid
        ("How many products?", None),  # Valid
    ]
    
    for invalid_query, fallback_query in queries:
        print(f"\nTrying: {invalid_query}")
        result = await agent.query(invalid_query)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            
            if fallback_query:
                print(f"Trying fallback: {fallback_query}")
                result = await agent.query(fallback_query)
                print(f"✅ Success: {result['natural_response']}")
        else:
            print(f"✅ Success: {result['natural_response']}")
    
    # Show stats
    stats = agent.get_stats()
    print(f"\n📊 Stats:")
    print(f"Total queries: {stats['total_queries']}")
    print(f"Successful: {stats['successful_queries']}")
    print(f"Failed: {stats['failed_queries']}")
    
    agent.close()


async def example_7_custom_workflow():
    """Example 7: Custom workflow with multiple agents."""
    print("\n" + "="*60)
    print("Example 7: Custom Workflow")
    print("="*60)
    
    # Create specialized agents
    analytics_agent = DatabaseQueryAgent.from_env(
        allowed_tables=["users", "orders", "products"],
        enable_statistics=True
    )
    
    reporting_agent = DatabaseQueryAgent.from_env(
        allowed_tables=["reports", "metrics"],
        enable_statistics=True
    )
    
    # Analytics workflow
    print("\n📊 Analytics Agent:")
    analytics_questions = [
        "How many users?",
        "Total orders?",
        "Top products?"
    ]
    
    for question in analytics_questions:
        result = await analytics_agent.query(question)
        print(f"  {question} → {result['natural_response']}")
    
    # Reporting workflow
    print("\n📈 Reporting Agent:")
    reporting_questions = [
        "Show latest reports",
        "What are the key metrics?"
    ]
    
    for question in reporting_questions:
        result = await reporting_agent.query(question)
        print(f"  {question} → {result['natural_response']}")
    
    # Compare stats
    print("\n📊 Agent Statistics:")
    print(f"Analytics: {analytics_agent.get_stats()['total_queries']} queries")
    print(f"Reporting: {reporting_agent.get_stats()['total_queries']} queries")
    
    # Cleanup
    analytics_agent.close()
    reporting_agent.close()


async def example_8_performance_monitoring():
    """Example 8: Monitor performance metrics."""
    print("\n" + "="*60)
    print("Example 8: Performance Monitoring")
    print("="*60)
    
    agent = DatabaseQueryAgent.from_env(
        enable_statistics=True,
        enable_cache=True
    )
    
    # Execute queries and track performance
    queries = [
        "How many users?",
        "How many orders?",
        "How many users?",  # Duplicate for cache hit
        "Top products?",
        "How many orders?",  # Duplicate for cache hit
    ]
    
    execution_times = []
    
    for i, question in enumerate(queries, 1):
        start = time.time()
        result = await agent.query(question)
        exec_time = time.time() - start
        execution_times.append(exec_time)
        
        print(f"\n{i}. {question}")
        print(f"   Time: {exec_time:.3f}s")
        print(f"   Answer: {result['natural_response']}")
    
    # Performance summary
    stats = agent.get_stats()
    
    print(f"\n📊 Performance Summary:")
    print(f"Total queries: {len(queries)}")
    print(f"Average time: {sum(execution_times)/len(execution_times):.3f}s")
    print(f"Min time: {min(execution_times):.3f}s")
    print(f"Max time: {max(execution_times):.3f}s")
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Cache hit rate: {(stats['cache_hits']/stats['total_queries']*100):.1f}%")
    
    # Connection pool stats
    pool_stats = stats['pool']
    print(f"\n🔌 Connection Pool:")
    print(f"Size: {pool_stats.get('size', 'N/A')}")
    print(f"Checked out: {pool_stats.get('checked_out', 'N/A')}")
    
    agent.close()


async def main():
    """Run all advanced examples."""
    print("\n" + "="*60)
    print("DB Query Agent - Advanced Usage Examples")
    print("="*60)
    
    # Run examples
    await example_1_batch_queries()
    await example_2_concurrent_queries()
    await example_3_streaming_with_processing()
    await example_4_session_management()
    await example_5_caching_strategies()
    await example_6_error_recovery()
    await example_7_custom_workflow()
    await example_8_performance_monitoring()
    
    print("\n" + "="*60)
    print("All advanced examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
