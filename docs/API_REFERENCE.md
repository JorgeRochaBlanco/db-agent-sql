# API Reference

Complete API documentation for `db-query-agent` package.

---

## Table of Contents

- [DatabaseQueryAgent](#databasequeryagent)
- [ChatSession](#chatsession)
- [Configuration Classes](#configuration-classes)
- [Exceptions](#exceptions)
- [Utility Functions](#utility-functions)

---

## DatabaseQueryAgent

The main interface for natural language database querying.

### Class: `DatabaseQueryAgent`

```python
from db_query_agent import DatabaseQueryAgent
```

#### Constructor

```python
DatabaseQueryAgent(
    database_url: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    # Model configuration
    model_strategy: Optional[str] = None,
    fast_model: Optional[str] = None,
    balanced_model: Optional[str] = None,
    complex_model: Optional[str] = None,
    # Cache configuration
    enable_cache: Optional[bool] = None,
    cache_backend: Optional[str] = None,
    schema_cache_ttl: Optional[int] = None,
    query_cache_ttl: Optional[int] = None,
    llm_cache_ttl: Optional[int] = None,
    # Safety configuration
    read_only: Optional[bool] = None,
    allowed_tables: Optional[list[str]] = None,
    blocked_tables: Optional[list[str]] = None,
    max_query_timeout: Optional[int] = None,
    max_result_rows: Optional[int] = None,
    # Connection configuration
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    # Performance configuration
    lazy_schema_loading: Optional[bool] = None,
    max_tables_in_context: Optional[int] = None,
    warmup_on_init: Optional[bool] = None,
    # Statistics configuration
    enable_statistics: bool = True,
    # Streaming configuration
    enable_streaming: Optional[bool] = None,
    # Session configuration
    session_backend: Optional[str] = None,
    session_db_path: Optional[str] = None,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `database_url` | `str` | From `.env` | Database connection URL (e.g., `postgresql://user:pass@host/db`) |
| `openai_api_key` | `str` | From `.env` | OpenAI API key |
| `model_strategy` | `str` | `"adaptive"` | Model selection strategy: `"adaptive"` or `"fixed"` |
| `fast_model` | `str` | `"gpt-4o-mini"` | Fast model for simple queries |
| `balanced_model` | `str` | `"gpt-4.1-mini"` | Balanced model |
| `complex_model` | `str` | `"gpt-4.1"` | Complex model for hard queries |
| `enable_cache` | `bool` | `True` | Enable caching |
| `cache_backend` | `str` | `"memory"` | Cache backend: `"memory"`, `"sqlite"`, `"redis"` |
| `schema_cache_ttl` | `int` | `3600` | Schema cache TTL in seconds |
| `query_cache_ttl` | `int` | `300` | Query result cache TTL in seconds |
| `llm_cache_ttl` | `int` | `3600` | LLM response cache TTL in seconds |
| `read_only` | `bool` | `True` | Only allow SELECT queries |
| `allowed_tables` | `list[str]` | `None` | List of allowed tables (None = all) |
| `blocked_tables` | `list[str]` | `None` | List of blocked tables |
| `max_query_timeout` | `int` | `30` | Maximum query execution time in seconds |
| `max_result_rows` | `int` | `10000` | Maximum result rows |
| `pool_size` | `int` | `10` | Connection pool size |
| `max_overflow` | `int` | `20` | Maximum overflow connections |
| `lazy_schema_loading` | `bool` | `True` | Load only relevant tables |
| `max_tables_in_context` | `int` | `5` | Max tables to include in context |
| `warmup_on_init` | `bool` | `False` | Warm up cache on initialization |
| `enable_statistics` | `bool` | `True` | Track query statistics |
| `enable_streaming` | `bool` | `False` | Enable streaming responses |
| `session_backend` | `str` | `"sqlite"` | Session backend: `"sqlite"` or `"memory"` |
| `session_db_path` | `str` | `None` | Path to session database file |

**Example:**

```python
# Direct configuration
agent = DatabaseQueryAgent(
    database_url="postgresql://user:pass@localhost/mydb",
    openai_api_key="sk-...",
    enable_cache=True,
    enable_streaming=True,
    enable_statistics=True
)
```

---

### Class Method: `from_env()`

Create agent from environment variables with optional overrides.

```python
@classmethod
DatabaseQueryAgent.from_env(**overrides) -> DatabaseQueryAgent
```

**Parameters:**
- `**overrides`: Any parameters to override from `.env`

**Returns:**
- `DatabaseQueryAgent` instance

**Example:**

```python
# Load everything from .env
agent = DatabaseQueryAgent.from_env()

# Override specific values
agent = DatabaseQueryAgent.from_env(
    read_only=False,
    fast_model="gpt-4.1",
    enable_streaming=True
)
```

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | Database connection URL |
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `MODEL_STRATEGY` | `"adaptive"` | Model selection strategy |
| `FAST_MODEL` | `"gpt-4o-mini"` | Fast model name |
| `BALANCED_MODEL` | `"gpt-4.1-mini"` | Balanced model name |
| `COMPLEX_MODEL` | `"gpt-4.1"` | Complex model name |
| `CACHE_ENABLED` | `"true"` | Enable caching |
| `CACHE_BACKEND` | `"memory"` | Cache backend |
| `CACHE_SCHEMA_TTL` | `"3600"` | Schema cache TTL |
| `CACHE_QUERY_TTL` | `"300"` | Query cache TTL |
| `CACHE_LLM_TTL` | `"3600"` | LLM cache TTL |
| `READ_ONLY` | `"true"` | Read-only mode |
| `QUERY_TIMEOUT` | `"30"` | Query timeout in seconds |
| `MAX_RESULT_ROWS` | `"10000"` | Max result rows |
| `DB_POOL_SIZE` | `"10"` | Connection pool size |
| `DB_MAX_OVERFLOW` | `"20"` | Max overflow connections |
| `ENABLE_STREAMING` | `"false"` | Enable streaming |
| `LAZY_SCHEMA_LOADING` | `"true"` | Lazy schema loading |
| `MAX_TABLES_IN_CONTEXT` | `"5"` | Max tables in context |
| `WARMUP_ON_INIT` | `"false"` | Warm up on init |

---

### Method: `query()`

Query database using natural language.

```python
async def query(
    question: str,
    return_sql: bool = True,
    return_results: bool = True,
    return_natural_response: bool = True,
    session: Optional[Any] = None
) -> Dict[str, Any]
```

**Parameters:**
- `question` (`str`): Natural language question
- `return_sql` (`bool`): Include SQL in response (default: `True`)
- `return_results` (`bool`): Execute query and return results (default: `True`)
- `return_natural_response` (`bool`): Generate natural language response (default: `True`)
- `session` (`Optional[Any]`): Optional session for conversation history

**Returns:**
- `Dict[str, Any]`: Dictionary with query results

**Response Format:**

```python
{
    "question": "How many users do we have?",
    "natural_response": "You have 150 users in your database.",
    "final_output": "You have 150 users in your database.",
    "sql": "SELECT COUNT(*) FROM users",
    "results": [{"count": 150}],
    "execution_time": 1.23,
    "is_casual": False,  # True if casual conversation
    "agent_used": "Conversational Agent"
}
```

**Example:**

```python
import asyncio

# Simple query
result = await agent.query("How many users do we have?")
print(result["natural_response"])
# "You have 150 users in your database."

# With session for conversation
session = agent.create_session("user_123")
result1 = await agent.query("Show me all users", session=session.session)
result2 = await agent.query("Filter by active users", session=session.session)
```

---

### Method: `query_stream()`

Query database with streaming response (token-by-token).

```python
async def query_stream(
    question: str,
    session: Optional[Any] = None
) -> AsyncIterator[str]
```

**Parameters:**
- `question` (`str`): Natural language question
- `session` (`Optional[Any]`): Optional session for conversation history

**Yields:**
- `str`: Response tokens as they are generated

**Example:**

```python
# Enable streaming first
agent = DatabaseQueryAgent.from_env(enable_streaming=True)

# Stream responses
async for chunk in agent.query_stream("How many orders do we have?"):
    print(chunk, end="", flush=True)
# Output: "You have 1,234 orders in your database."

# With session
session = agent.create_session("user_123")
async for chunk in agent.query_stream("Show top products", session=session.session):
    print(chunk, end="", flush=True)
```

---

### Method: `create_session()`

Create a chat session for multi-turn conversations.

```python
def create_session(session_id: str) -> ChatSession
```

**Parameters:**
- `session_id` (`str`): Unique session identifier

**Returns:**
- `ChatSession`: ChatSession instance

**Example:**

```python
# Create session
session = agent.create_session("user_123")

# Use session for conversation
result1 = await session.ask("How many users?")
result2 = await session.ask("Show me the top 10")
result3 = await session.ask("Filter by active")
```

---

### Method: `get_schema()`

Get database schema.

```python
def get_schema() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Database schema

**Example:**

```python
schema = agent.get_schema()
print(schema.keys())
# dict_keys(['users', 'orders', 'products'])
```

---

### Method: `get_schema_info()`

Get detailed database schema information.

```python
def get_schema_info(include_foreign_keys: bool = True) -> Dict[str, Any]
```

**Parameters:**
- `include_foreign_keys` (`bool`): Include foreign key relationships (default: `True`)

**Returns:**
- `Dict[str, Any]`: Comprehensive schema information

**Response Format:**

```python
{
    "total_tables": 3,
    "tables": {
        "users": {
            "name": "users",
            "columns": [
                {"name": "id", "type": "INTEGER", "primary_key": True},
                {"name": "name", "type": "VARCHAR(100)"}
            ],
            "primary_keys": ["id"],
            "foreign_keys": [],
            "indexes": []
        },
        "orders": {
            "name": "orders",
            "columns": [...],
            "primary_keys": ["id"],
            "foreign_keys": [
                {
                    "constrained_columns": ["user_id"],
                    "referred_table": "users",
                    "referred_columns": ["id"]
                }
            ],
            "indexes": []
        }
    },
    "relationships": [
        {
            "from_table": "orders",
            "from_columns": ["user_id"],
            "to_table": "users",
            "to_columns": ["id"]
        }
    ]
}
```

**Example:**

```python
# Get full schema info
schema_info = agent.get_schema_info(include_foreign_keys=True)
print(f"Total tables: {schema_info['total_tables']}")
print(f"Relationships: {len(schema_info['relationships'])}")

# Get basic schema (faster)
schema_info = agent.get_schema_info(include_foreign_keys=False)
```

---

### Method: `get_stats()`

Get agent statistics.

```python
def get_stats() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Comprehensive statistics

**Response Format:**

```python
{
    # Query statistics (if enabled)
    "total_queries": 42,
    "successful_queries": 40,
    "failed_queries": 2,
    "cache_hits": 15,
    
    # Cache statistics
    "cache": {
        "total_entries": 25,
        "active_entries": 20,
        "expired_entries": 5
    },
    
    # Connection pool statistics
    "pool": {
        "size": 10,
        "checked_out": 2,
        "overflow": 0
    },
    
    # Session statistics
    "sessions": {
        "total_sessions": 5,
        "backend": "sqlite",
        "db_path": "./sessions.db"
    },
    
    # Schema info
    "schema_tables": 10
}
```

**Example:**

```python
stats = agent.get_stats()

# Calculate cache hit rate
if stats["total_queries"] > 0:
    hit_rate = (stats["cache_hits"] / stats["total_queries"]) * 100
    print(f"Cache hit rate: {hit_rate:.1f}%")
```

---

### Method: `list_sessions()`

List all active session IDs.

```python
def list_sessions() -> list[str]
```

**Returns:**
- `list[str]`: List of session IDs

**Example:**

```python
sessions = agent.list_sessions()
print(sessions)
# ['user_123', 'user_456', 'admin_session']
```

---

### Method: `get_session_history()`

Get conversation history for a session.

```python
def get_session_history(session_id: str) -> Optional[list[Dict[str, Any]]]
```

**Parameters:**
- `session_id` (`str`): Session identifier

**Returns:**
- `Optional[list[Dict[str, Any]]]`: List of conversation messages or `None` if session not found

**Example:**

```python
history = agent.get_session_history("user_123")
if history:
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")
```

---

### Method: `clear_session()`

Clear a session's conversation history.

```python
def clear_session(session_id: str) -> None
```

**Parameters:**
- `session_id` (`str`): Session identifier

**Example:**

```python
agent.clear_session("user_123")
```

---

### Method: `delete_session()`

Delete a session.

```python
def delete_session(session_id: str) -> None
```

**Parameters:**
- `session_id` (`str`): Session identifier

**Example:**

```python
agent.delete_session("user_123")
```

---

### Method: `close()`

Close all connections and cleanup.

```python
def close() -> None
```

**Example:**

```python
agent.close()
```

---

## ChatSession

Wrapper for chat-like interface with session.

### Class: `ChatSession`

```python
from db_query_agent import ChatSession
```

#### Constructor

```python
ChatSession(
    session_id: str,
    agent: DatabaseQueryAgent,
    session: SessionABC
)
```

**Note:** Use `agent.create_session()` instead of creating directly.

---

### Method: `ask()`

Ask a question in the session context with memory.

```python
async def ask(question: str) -> Dict[str, Any]
```

**Parameters:**
- `question` (`str`): User's question

**Returns:**
- `Dict[str, Any]`: Response dictionary

**Example:**

```python
session = agent.create_session("user_123")

# Multi-turn conversation
result1 = await session.ask("How many users do we have?")
result2 = await session.ask("Show me the top 10")  # Remembers context
result3 = await session.ask("Filter by active")    # Remembers context
```

---

### Method: `clear()`

Clear session history.

```python
async def clear() -> None
```

**Example:**

```python
await session.clear()
```

---

## Configuration Classes

### DatabaseConfig

```python
from db_query_agent import DatabaseConfig

config = DatabaseConfig(
    url="postgresql://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    ssl_enabled=True,
    ssl_verify=True
)
```

### CacheConfig

```python
from db_query_agent import CacheConfig

config = CacheConfig(
    enabled=True,
    backend="memory",  # or "sqlite", "redis"
    schema_ttl=3600,
    query_ttl=300,
    llm_ttl=3600,
    redis_url="redis://localhost:6379"  # if using redis
)
```

### ModelConfig

```python
from db_query_agent import ModelConfig

config = ModelConfig(
    strategy="adaptive",  # or "fixed"
    fast_model="gpt-4o-mini",
    balanced_model="gpt-4.1-mini",
    complex_model="gpt-4.1",
    temperature=0.0,
    max_tokens=1000
)
```

### SafetyConfig

```python
from db_query_agent import SafetyConfig

config = SafetyConfig(
    read_only=True,
    allowed_tables=["users", "orders"],  # None = all tables
    blocked_tables=["sensitive_data"],
    max_query_timeout=30,
    max_result_rows=10000,
    enable_guardrails=True
)
```

### AgentConfig

```python
from db_query_agent import AgentConfig, DatabaseConfig, CacheConfig

config = AgentConfig(
    openai_api_key="sk-...",
    database=DatabaseConfig(url="postgresql://..."),
    cache=CacheConfig(enabled=True),
    model=ModelConfig(strategy="adaptive"),
    safety=SafetyConfig(read_only=True),
    enable_streaming=True,
    lazy_schema_loading=True,
    max_tables_in_context=5
)
```

---

## Exceptions

All exceptions inherit from `DatabaseQueryAgentError`.

### DatabaseQueryAgentError

Base exception for all db-query-agent errors.

```python
from db_query_agent import DatabaseQueryAgentError

try:
    result = await agent.query("invalid query")
except DatabaseQueryAgentError as e:
    print(f"Error: {e}")
```

### ValidationError

Raised when query validation fails.

```python
from db_query_agent import ValidationError

try:
    result = await agent.query("DROP TABLE users")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### QueryExecutionError

Raised when query execution fails.

```python
from db_query_agent import QueryExecutionError

try:
    result = await agent.query("SELECT * FROM nonexistent_table")
except QueryExecutionError as e:
    print(f"Execution failed: {e}")
```

### SchemaExtractionError

Raised when schema extraction fails.

```python
from db_query_agent import SchemaExtractionError
```

---

## Utility Functions

### get_env()

Get environment variable with optional default.

```python
from db_query_agent.config import get_env

api_key = get_env("OPENAI_API_KEY")
db_url = get_env("DATABASE_URL", "sqlite:///:memory:")
```

---

## Complete Example

```python
import asyncio
from db_query_agent import DatabaseQueryAgent

async def main():
    # Create agent from .env
    agent = DatabaseQueryAgent.from_env(
        enable_streaming=True,
        enable_statistics=True
    )
    
    # Simple query
    result = await agent.query("How many users do we have?")
    print(result["natural_response"])
    
    # Streaming query
    print("\nStreaming response:")
    async for chunk in agent.query_stream("Show top 10 products by price"):
        print(chunk, end="", flush=True)
    print()
    
    # Session-based conversation
    session = agent.create_session("user_123")
    result1 = await session.ask("How many orders?")
    result2 = await session.ask("Show me the recent ones")
    
    # Get statistics
    stats = agent.get_stats()
    print(f"\nTotal queries: {stats['total_queries']}")
    print(f"Cache hits: {stats['cache_hits']}")
    
    # Cleanup
    agent.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## See Also

- [Integration Guides](INTEGRATION_GUIDES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Examples](../examples/)
