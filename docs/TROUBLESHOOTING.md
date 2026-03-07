# Troubleshooting Guide

Common issues and solutions for `db-query-agent`.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Issues](#connection-issues)
- [Query Issues](#query-issues)
- [Performance Issues](#performance-issues)
- [Streaming Issues](#streaming-issues)
- [Session Issues](#session-issues)
- [Configuration Issues](#configuration-issues)

---

## Installation Issues

### Issue: `ModuleNotFoundError: No module named 'db_query_agent'`

**Cause:** Package not installed or installed in wrong environment.

**Solution:**

```bash
# Make sure you're in the correct virtual environment
pip install db-query-agent

# Or install in development mode
pip install -e .
```

### Issue: `ImportError: cannot import name 'DatabaseQueryAgent'`

**Cause:** Outdated package version or incorrect import.

**Solution:**

```python
# Correct import
from db_query_agent import DatabaseQueryAgent

# Not this
from db_query_agent.agent import DatabaseQueryAgent  # Wrong
```

Update package:
```bash
pip install --upgrade db-query-agent
```

### Issue: Dependency conflicts

**Cause:** Conflicting package versions.

**Solution:**

```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install db-query-agent
```

---

## Connection Issues

### Issue: `ConnectionError: Failed to create database engine`

**Cause:** Invalid database URL or database not accessible.

**Solution:**

1. **Check database URL format:**

```python
# PostgreSQL
database_url = "postgresql://user:password@localhost:5432/dbname"

# MySQL
database_url = "mysql+pymysql://user:password@localhost:3306/dbname"

# SQLite
database_url = "sqlite:///path/to/database.db"
database_url = "sqlite:///:memory:"  # In-memory
```

2. **Test connection manually:**

```python
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/db")
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print(result.fetchone())
```

3. **Check database is running:**

```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# MySQL
mysqladmin ping -h localhost
```

4. **Check firewall/network:**

```bash
# Test connection
telnet localhost 5432  # PostgreSQL
telnet localhost 3306  # MySQL
```

### Issue: `No module named 'psycopg2'` or `'pymysql'`

**Cause:** Database driver not installed.

**Solution:**

```bash
# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install pymysql

# SQL Server
pip install pyodbc
```

### Issue: SSL connection errors

**Cause:** SSL configuration mismatch.

**Solution:**

```python
# Disable SSL verification (development only!)
agent = DatabaseQueryAgent(
    database_url="postgresql://user:pass@localhost/db?sslmode=disable"
)

# Or configure SSL properly
agent = DatabaseQueryAgent(
    database_url="postgresql://user:pass@localhost/db",
    ssl_enabled=True,
    ssl_cert="/path/to/cert.pem",
    ssl_key="/path/to/key.pem",
    ssl_ca="/path/to/ca.pem"
)
```

---

## Query Issues

### Issue: `ValidationError: Query validation failed`

**Cause:** Query violates safety rules (e.g., trying to use DROP, DELETE in read-only mode).

**Solution:**

1. **Check read-only mode:**

```python
# If you need write access
agent = DatabaseQueryAgent.from_env(read_only=False)
```

2. **Check allowed/blocked tables:**

```python
# Allow specific tables
agent = DatabaseQueryAgent.from_env(
    allowed_tables=["users", "orders", "products"]
)

# Block specific tables
agent = DatabaseQueryAgent.from_env(
    blocked_tables=["sensitive_data", "admin_logs"]
)
```

### Issue: Incorrect SQL generated

**Cause:** Ambiguous question or insufficient schema context.

**Solution:**

1. **Be more specific:**

```python
# Vague
await agent.query("Show me data")

# Specific
await agent.query("Show me all users created in the last 7 days")
```

2. **Use sessions for context:**

```python
session = agent.create_session("user_123")
await session.ask("Show me users")
await session.ask("Filter by active status")  # Remembers context
```

3. **Check schema is correct:**

```python
schema = agent.get_schema()
print(schema.keys())  # Verify tables are loaded
```

### Issue: `QueryExecutionError: Query execution failed`

**Cause:** Generated SQL is invalid for your database.

**Solution:**

1. **Check the SQL:**

```python
result = await agent.query("your question")
print(result.get('sql'))  # Inspect generated SQL
```

2. **Test SQL manually:**

```python
# Test the SQL directly
sql = result['sql']
results = agent.connection_manager.execute_query(sql)
```

3. **Report issue with details:**

```python
# Get full error details
import logging
logging.basicConfig(level=logging.DEBUG)

result = await agent.query("your question")
```

### Issue: Empty results when data exists

**Cause:** Incorrect WHERE clause or table filtering.

**Solution:**

1. **Check query without filters:**

```python
await agent.query("Show all users")  # No filters
await agent.query("Count all users")  # Verify data exists
```

2. **Verify table names:**

```python
schema_info = agent.get_schema_info()
print(list(schema_info['tables'].keys()))
```

---

## Performance Issues

### Issue: Queries are slow (> 5 seconds)

**Cause:** Large schema, no caching, or complex queries.

**Solution:**

1. **Enable caching:**

```python
agent = DatabaseQueryAgent.from_env(
    enable_cache=True,
    schema_cache_ttl=3600,  # 1 hour
    query_cache_ttl=300,    # 5 minutes
    llm_cache_ttl=3600      # 1 hour
)
```

2. **Use lazy schema loading:**

```python
agent = DatabaseQueryAgent.from_env(
    lazy_schema_loading=True,
    max_tables_in_context=5  # Limit tables in context
)
```

3. **Warm up cache:**

```python
agent = DatabaseQueryAgent.from_env(warmup_on_init=True)
```

4. **Check statistics:**

```python
stats = agent.get_stats()
print(f"Cache hit rate: {stats['cache_hits']/stats['total_queries']*100:.1f}%")
```

### Issue: High memory usage

**Cause:** Large result sets or too many cached items.

**Solution:**

1. **Limit result rows:**

```python
agent = DatabaseQueryAgent.from_env(
    max_result_rows=1000  # Limit to 1000 rows
)
```

2. **Reduce cache TTL:**

```python
agent = DatabaseQueryAgent.from_env(
    schema_cache_ttl=600,   # 10 minutes
    query_cache_ttl=60,     # 1 minute
    llm_cache_ttl=600       # 10 minutes
)
```

3. **Use Redis for caching:**

```python
agent = DatabaseQueryAgent.from_env(
    cache_backend="redis",
    redis_url="redis://localhost:6379"
)
```

### Issue: Connection pool exhausted

**Cause:** Too many concurrent queries.

**Solution:**

```python
agent = DatabaseQueryAgent.from_env(
    pool_size=20,        # Increase pool size
    max_overflow=40      # Increase overflow
)
```

---

## Streaming Issues

### Issue: Streaming not working

**Cause:** Streaming not enabled or incorrect usage.

**Solution:**

1. **Enable streaming:**

```python
agent = DatabaseQueryAgent.from_env(enable_streaming=True)
```

2. **Use async iteration:**

```python
# Correct
async for chunk in agent.query_stream("question"):
    print(chunk, end="", flush=True)

# Wrong
result = agent.query_stream("question")  # Missing async for
```

3. **Check event loop:**

```python
import asyncio

async def main():
    async for chunk in agent.query_stream("question"):
        print(chunk, end="")

asyncio.run(main())
```

### Issue: Streaming is too fast/slow

**Cause:** Default streaming speed.

**Solution:**

Add artificial delay in your code:

```python
import asyncio

async for chunk in agent.query_stream("question"):
    print(chunk, end="", flush=True)
    await asyncio.sleep(0.03)  # 30ms delay per token
```

### Issue: Streaming stops mid-response

**Cause:** Network timeout or error in streaming.

**Solution:**

1. **Check logs:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Handle errors:**

```python
try:
    async for chunk in agent.query_stream("question"):
        print(chunk, end="")
except Exception as e:
    print(f"\nError: {e}")
```

---

## Session Issues

### Issue: Session not remembering context

**Cause:** Not using session correctly or session cleared.

**Solution:**

1. **Use session object:**

```python
# Create session
session = agent.create_session("user_123")

# Use session.session for queries
result = await agent.query("question", session=session.session)

# Or use session.ask()
result = await session.ask("question")
```

2. **Check session exists:**

```python
sessions = agent.list_sessions()
print(sessions)  # Verify your session is listed
```

3. **Don't clear session accidentally:**

```python
# This clears history
agent.clear_session("user_123")

# This deletes session
agent.delete_session("user_123")
```

### Issue: Too many sessions consuming memory

**Cause:** Sessions not being cleaned up.

**Solution:**

1. **Delete old sessions:**

```python
# List sessions
sessions = agent.list_sessions()

# Delete old ones
for session_id in sessions:
    if should_delete(session_id):
        agent.delete_session(session_id)
```

2. **Use session expiration:**

```python
# Implement custom session cleanup
import time

session_timestamps = {}

def cleanup_old_sessions(max_age=3600):
    """Delete sessions older than max_age seconds."""
    current_time = time.time()
    for session_id, timestamp in list(session_timestamps.items()):
        if current_time - timestamp > max_age:
            agent.delete_session(session_id)
            del session_timestamps[session_id]
```

---

## Configuration Issues

### Issue: `.env` file not being loaded

**Cause:** File not in correct location or not named correctly.

**Solution:**

1. **Check file location:**

```bash
# .env should be in project root
project/
├── .env          # Here
├── main.py
└── ...
```

2. **Check file name:**

```bash
# Must be exactly .env (not .env.txt or env)
ls -la | grep .env
```

3. **Load manually:**

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file

agent = DatabaseQueryAgent.from_env()
```

4. **Check environment variables:**

```python
import os
print(os.getenv('DATABASE_URL'))
print(os.getenv('OPENAI_API_KEY'))
```

### Issue: `ValueError: OPENAI_API_KEY must be provided`

**Cause:** API key not set.

**Solution:**

1. **Set in .env:**

```bash
# .env
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://...
```

2. **Or pass directly:**

```python
agent = DatabaseQueryAgent(
    database_url="postgresql://...",
    openai_api_key="sk-your-key-here"
)
```

3. **Or set environment variable:**

```bash
export OPENAI_API_KEY=sk-your-key-here
export DATABASE_URL=postgresql://...
```

### Issue: Configuration not taking effect

**Cause:** Parameter override order.

**Solution:**

Remember the priority: **Parameter > .env > Default**

```python
# .env has CACHE_ENABLED=true
# But this overrides it:
agent = DatabaseQueryAgent.from_env(
    enable_cache=False  # This takes precedence
)
```

---

## Error Messages

### Common Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `No module named 'db_query_agent'` | Not installed | `pip install db-query-agent` |
| `ConnectionError: Failed to create database engine` | Invalid DB URL | Check database URL format |
| `ValidationError: Query validation failed` | Safety violation | Check read_only mode and allowed tables |
| `QueryExecutionError: Query execution failed` | Invalid SQL | Check generated SQL |
| `ValueError: OPENAI_API_KEY must be provided` | Missing API key | Set in .env or pass as parameter |
| `SchemaExtractionError` | Can't read schema | Check database permissions |
| `CacheError` | Cache operation failed | Check cache backend configuration |

---

## Debug Mode

Enable debug logging to see detailed information:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now run your code
agent = DatabaseQueryAgent.from_env()
result = await agent.query("your question")
```

---

## Getting Help

If you're still stuck:

1. **Check logs:** Enable debug logging and check error messages
2. **Check GitHub Issues:** Search for similar issues
3. **Create an issue:** Include:
   - Error message
   - Full traceback
   - Minimal reproducible example
   - Environment details (Python version, OS, database type)

---

## See Also

- [API Reference](API_REFERENCE.md)
- [Integration Guides](INTEGRATION_GUIDES.md)
- [Examples](../examples/)
