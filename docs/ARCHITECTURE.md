# Architecture

System architecture and design decisions for `db-query-agent`.

---

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Configuration System](#configuration-system)
- [Caching Strategy](#caching-strategy)
- [Session Management](#session-management)
- [Security Model](#security-model)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DatabaseQueryAgent                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Configuration │  │  Statistics  │  │   Sessions   │          │
│  │   Manager    │  │   Tracker    │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Multi-Agent System (Conversational)              │  │
│  │                                                            │  │
│  │  ┌────────────────┐         ┌────────────────┐          │  │
│  │  │ Conversational │  ◄────► │  SQL Agent     │          │  │
│  │  │     Agent      │         │   (as tool)    │          │  │
│  │  └────────────────┘         └────────────────┘          │  │
│  │         │                            │                    │  │
│  │         └────────────────────────────┘                    │  │
│  │                      │                                     │  │
│  │                      ▼                                     │  │
│  │           ┌──────────────────────┐                        │  │
│  │           │   Database Context   │                        │  │
│  │           └──────────────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Schema     │  │    Cache     │  │  Connection  │          │
│  │  Extractor   │  │   Manager    │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Database │      │  Cache   │      │ Database │
    │  Schema  │      │ Storage  │      │   Pool   │
    └──────────┘      └──────────┘      └──────────┘
```

---

## Component Architecture

### 1. DatabaseQueryAgent (Main Interface)

**Responsibilities:**
- Expose simple API for users
- Coordinate between components
- Manage lifecycle and cleanup
- Track statistics (optional)

**Key Methods:**
- `query()` - Execute queries
- `query_stream()` - Stream responses
- `create_session()` - Create chat sessions
- `get_schema()` - Get database schema
- `get_stats()` - Get statistics

### 2. Multi-Agent System

**Architecture:**
```
Conversational Agent (Main)
    │
    ├─► SQL Agent (Tool)
    │   ├─► execute_query()
    │   └─► validate_query()
    │
    └─► Database Context
        ├─► Schema Extractor
        ├─► Query Validator
        └─► Connection Manager
```

**Design Decision:**
- Single conversational agent with SQL agent as a tool
- 1 LLM call per query (optimized for speed)
- Handles both casual conversation and SQL queries
- Automatic context management

### 3. Configuration System

**Three-Layer Configuration:**

```
┌─────────────────────────────────────┐
│     1. Direct Parameters            │  ← Highest Priority
│  DatabaseQueryAgent(enable_cache=..)│
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│     2. Environment Variables        │  ← Medium Priority
│  DATABASE_URL=...                   │
│  OPENAI_API_KEY=...                 │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│     3. Default Values               │  ← Lowest Priority
│  enable_cache=True                  │
│  read_only=True                     │
└─────────────────────────────────────┘
```

**Configuration Classes:**
- `AgentConfig` - Main configuration
- `DatabaseConfig` - Database settings
- `CacheConfig` - Cache settings
- `ModelConfig` - LLM model settings
- `SafetyConfig` - Security settings

### 4. Schema Extractor

**Responsibilities:**
- Extract database schema
- Cache schema information
- Provide schema context to agents

**Features:**
- Supports PostgreSQL, MySQL, SQLite, SQL Server
- Extracts tables, columns, types, keys, indexes
- Foreign key relationship mapping
- Lazy loading for large databases

### 5. Cache Manager

**Three-Level Caching:**

```
┌──────────────────────────────────┐
│  1. Schema Cache (TTL: 1 hour)   │
│     - Table definitions          │
│     - Column information         │
│     - Relationships              │
└──────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│  2. LLM Response Cache           │
│     (TTL: 1 hour)                │
│     - Question → Response        │
│     - Keyed by question + schema │
└──────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────┐
│  3. Query Result Cache           │
│     (TTL: 5 minutes)             │
│     - SQL → Results              │
│     - Keyed by SQL query         │
└──────────────────────────────────┘
```

**Backends:**
- Memory (default) - Fast, in-process
- SQLite - Persistent, file-based
- Redis - Distributed, scalable

### 6. Connection Manager

**Connection Pooling:**

```
┌─────────────────────────────────────┐
│      Connection Pool                │
│                                     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐      │
│  │Conn│ │Conn│ │Conn│ │Conn│ ...  │
│  └────┘ └────┘ └────┘ └────┘      │
│                                     │
│  Pool Size: 10                      │
│  Max Overflow: 20                   │
│  Timeout: 30s                       │
└─────────────────────────────────────┘
```

**Features:**
- SQLAlchemy-based pooling
- Automatic connection recycling
- SSL support
- Timeout handling

### 7. Session Manager

**Session Storage:**

```
┌──────────────────────────────────┐
│     Session Manager              │
│                                  │
│  ┌────────────┐  ┌────────────┐ │
│  │ Session 1  │  │ Session 2  │ │
│  │            │  │            │ │
│  │ Messages:  │  │ Messages:  │ │
│  │ - User     │  │ - User     │ │
│  │ - AI       │  │ - AI       │ │
│  │ - User     │  │ - User     │ │
│  └────────────┘  └────────────┘ │
│                                  │
│  Backend: SQLite / Memory        │
└──────────────────────────────────┘
```

**Features:**
- OpenAI Agents SDK sessions
- SQLite backend (default)
- In-memory option
- Automatic history management

### 8. Query Validator

**Validation Pipeline:**

```
Input SQL
    │
    ▼
┌─────────────────┐
│ Parse SQL       │
│ (sqlparse)      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Check Read-Only │
│ (if enabled)    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Check Tables    │
│ (allow/block)   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Validate Syntax │
└─────────────────┘
    │
    ▼
Valid SQL ✓
```

---

## Data Flow

### Query Execution Flow

```
1. User Question
    │
    ▼
2. Check Cache
    │
    ├─► Cache Hit ──► Return Cached Response
    │
    └─► Cache Miss
        │
        ▼
3. Load Schema (cached)
    │
    ▼
4. Send to Conversational Agent
    │
    ├─► Casual Conversation ──► Return Response
    │
    └─► Database Query
        │
        ▼
5. SQL Agent (as tool)
    │
    ├─► Generate SQL
    │
    ├─► Validate SQL
    │
    ├─► Execute SQL
    │
    └─► Format Results
        │
        ▼
6. Generate Natural Response
    │
    ▼
7. Cache Response
    │
    ▼
8. Return to User
```

### Streaming Flow

```
1. User Question
    │
    ▼
2. Check Cache
    │
    ├─► Cache Hit ──► Yield Cached Response (instant)
    │
    └─► Cache Miss
        │
        ▼
3. Start Streaming
    │
    ▼
4. For each token:
    │
    ├─► Yield token
    │
    └─► Accumulate full response
        │
        ▼
5. Cache full response
    │
    ▼
6. Update statistics
```

---

## Configuration System

### Configuration Priority

```python
# Example: enable_cache resolution

# 1. Check direct parameter
agent = DatabaseQueryAgent(enable_cache=False)  # ← Used

# 2. If not provided, check .env
# CACHE_ENABLED=true  # ← Would be used if param not provided

# 3. If not in .env, use default
# Default: True  # ← Would be used if neither above provided
```

### Environment Variables

All configuration can be set via environment variables:

```bash
# Database
DATABASE_URL=postgresql://...
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# OpenAI
OPENAI_API_KEY=sk-...

# Models
MODEL_STRATEGY=adaptive
FAST_MODEL=gpt-4o-mini
BALANCED_MODEL=gpt-4.1-mini
COMPLEX_MODEL=gpt-4.1

# Cache
CACHE_ENABLED=true
CACHE_BACKEND=memory
CACHE_SCHEMA_TTL=3600
CACHE_QUERY_TTL=300
CACHE_LLM_TTL=3600

# Safety
READ_ONLY=true
QUERY_TIMEOUT=30
MAX_RESULT_ROWS=10000

# Features
ENABLE_STREAMING=false
LAZY_SCHEMA_LOADING=true
MAX_TABLES_IN_CONTEXT=5
```

---

## Caching Strategy

### Cache Key Generation

```python
# Schema Cache
key = f"schema:{database_url_hash}"

# LLM Response Cache
key = f"llm:{hash(question)}:{hash(schema)}"

# Query Result Cache
key = f"query:{hash(sql)}"
```

### Cache Invalidation

- **Schema Cache:** TTL-based (default: 1 hour)
- **LLM Cache:** TTL-based (default: 1 hour)
- **Query Cache:** TTL-based (default: 5 minutes)

### Cache Backends

**Memory (Default):**
- Pros: Fast, no dependencies
- Cons: Not persistent, not shared
- Use case: Single-process applications

**SQLite:**
- Pros: Persistent, file-based
- Cons: Not distributed
- Use case: Single-server applications

**Redis:**
- Pros: Distributed, scalable, persistent
- Cons: Requires Redis server
- Use case: Multi-server applications

---

## Session Management

### Session Lifecycle

```
1. Create Session
   agent.create_session("user_123")
   │
   ▼
2. Use Session
   session.ask("question 1")
   session.ask("question 2")  # Remembers context
   │
   ▼
3. Clear History (optional)
   agent.clear_session("user_123")
   │
   ▼
4. Delete Session
   agent.delete_session("user_123")
```

### Session Storage

**SQLite Backend (Default):**
```
sessions.db
├── session_user_123
│   ├── message_1 (user)
│   ├── message_2 (assistant)
│   └── message_3 (user)
├── session_user_456
│   └── ...
```

**Memory Backend:**
- Stored in Python dict
- Lost on restart
- Faster access

---

## Security Model

### Defense Layers

```
1. Input Validation
   ├─► SQL Injection Prevention
   ├─► Prompt Injection Detection
   └─► Input Sanitization
   
2. Query Validation
   ├─► Read-Only Mode (default)
   ├─► Table Allowlist/Blocklist
   └─► Syntax Validation
   
3. Execution Controls
   ├─► Query Timeout (30s default)
   ├─► Result Row Limit (10k default)
   └─► Connection Pooling
   
4. Output Sanitization
   ├─► Result Formatting
   └─► Error Message Filtering
```

### Read-Only Mode

```python
# Default: read_only=True
# Only SELECT queries allowed

Allowed:
✓ SELECT * FROM users
✓ SELECT COUNT(*) FROM orders
✓ SELECT ... JOIN ... WHERE ...

Blocked:
✗ DROP TABLE users
✗ DELETE FROM users
✗ UPDATE users SET ...
✗ INSERT INTO users ...
✗ TRUNCATE TABLE users
```

### Table Access Control

```python
# Allowlist (whitelist)
agent = DatabaseQueryAgent.from_env(
    allowed_tables=["users", "orders", "products"]
)
# Only these tables can be queried

# Blocklist (blacklist)
agent = DatabaseQueryAgent.from_env(
    blocked_tables=["admin_logs", "sensitive_data"]
)
# These tables cannot be queried
```

---

## Performance Optimizations

### 1. Lazy Schema Loading

Only load relevant tables instead of entire schema:

```python
agent = DatabaseQueryAgent.from_env(
    lazy_schema_loading=True,
    max_tables_in_context=5
)
```

### 2. Connection Pooling

Reuse database connections:

```python
agent = DatabaseQueryAgent.from_env(
    pool_size=10,
    max_overflow=20
)
```

### 3. Multi-Level Caching

Cache at multiple levels:
- Schema (1 hour)
- LLM responses (1 hour)
- Query results (5 minutes)

### 4. Adaptive Model Selection

Use faster models for simple queries:
- Simple: gpt-4o-mini (2s)
- Complex: gpt-4.1 (5s)

---

## Scalability

### Horizontal Scaling

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Server 1 │  │ Server 2 │  │ Server 3 │
│          │  │          │  │          │
│  Agent   │  │  Agent   │  │  Agent   │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
            ┌──────▼──────┐
            │    Redis    │  ← Shared Cache
            │   (Cache)   │
            └─────────────┘
                   │
            ┌──────▼──────┐
            │  Database   │  ← Connection Pool
            │   (Pool)    │
            └─────────────┘
```

### Vertical Scaling

- Increase connection pool size
- Increase cache size
- Use faster models
- Add more CPU/RAM

---

## Design Decisions

### Why Single Conversational Agent?

**Pros:**
- 1 LLM call per query (faster)
- Simpler architecture
- Easier to maintain
- Better context handling

**Cons:**
- Less specialized
- Single point of failure

**Decision:** Speed and simplicity outweigh specialization.

### Why Three-Layer Configuration?

**Pros:**
- Flexible for different environments
- Easy to override in code
- Clear priority system

**Cons:**
- More complex to understand initially

**Decision:** Flexibility is critical for production use.

### Why Default Read-Only?

**Pros:**
- Safe by default
- Prevents accidental data modification
- Suitable for analytics use case

**Cons:**
- Need to explicitly enable writes

**Decision:** Safety first, opt-in for writes.

---

## See Also

- [API Reference](API_REFERENCE.md)
- [Integration Guides](INTEGRATION_GUIDES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
