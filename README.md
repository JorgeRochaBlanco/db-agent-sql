# DB Query Agent 🤖💬

> **AI-powered natural language database query system using OpenAI Agents SDK**

[![PyPI version](https://badge.fury.io/py/db-query-agent.svg)](https://badge.fury.io/py/db-query-agent)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/db-query-agent)](https://pepy.tech/project/db-query-agent)

A powerful, production-ready Python package that lets you query databases using natural language. Built with OpenAI Agents SDK, featuring intelligent safety guardrails, streaming responses, and optimized for speed.

## ✨ Features

- 🗣️ **Natural Language Queries** - Ask questions in plain English, get SQL and results
- ⚡ **Blazing Fast** - Streaming responses, adaptive model selection, multi-layer caching
- 🔒 **Production-Ready Safety** - Read-only mode, SQL injection prevention, query validation
- 💬 **Session Management** - Maintains conversation context across multiple queries
- 🎯 **Smart Schema Loading** - Only loads relevant tables for faster responses
- 🔌 **Universal Database Support** - PostgreSQL, MySQL, SQLite, SQL Server
- 📦 **Easy Integration** - Works with Django, Flask, FastAPI, or any Python app

## 🚀 Quick Start

### Installation

```bash
pip install db-query-agent

# With database-specific drivers
pip install db-query-agent[postgres]  # PostgreSQL
pip install db-query-agent[mysql]     # MySQL
pip install db-query-agent[all]       # All drivers
```

### Basic Usage

**Option 1: Load from .env (Recommended)**

```bash
# Create .env file
DATABASE_URL=postgresql://user:pass@localhost/mydb
OPENAI_API_KEY=sk-...
FAST_MODEL=gpt-4o-mini
READ_ONLY=true
```

```python
from db_query_agent import DatabaseQueryAgent

# Load everything from .env
agent = DatabaseQueryAgent.from_env()

# Or override specific values
agent = DatabaseQueryAgent.from_env(
    fast_model="gpt-4.1",
    enable_statistics=True
)
```

**Option 2: Direct Configuration**

```python
from db_query_agent import DatabaseQueryAgent

# Pass all parameters directly
agent = DatabaseQueryAgent(
    database_url="postgresql://user:pass@localhost/mydb",
    openai_api_key="sk-...",
    fast_model="gpt-4o-mini",
    read_only=True,
    enable_cache=True
)
```

### Query the Database

```python
# Query in natural language (async)
result = await agent.query("How many users signed up last month?")

print(result["natural_response"])
# Output: "245 users signed up last month"

print(result["sql"])
# Output: "SELECT COUNT(*) FROM users WHERE created_at >= '2025-09-01'"
```

### With Streaming (Recommended)

```python
# Stream responses for better UX
async for chunk in agent.query_stream("Show me top 10 customers by revenue"):
    print(chunk, end="", flush=True)
```

### Session-based Chat

```python
# Create a session for multi-turn conversations
session = agent.create_session(session_id="user_123")

# First query
response1 = await session.ask("Show me all products")

# Follow-up query (maintains context)
response2 = await session.ask("Filter those by category=electronics")

# Another follow-up
response3 = await session.ask("Sort by price descending")
```

## 🔧 Utility Methods

### Session Management

```python
# List all active sessions
sessions = agent.list_sessions()

# Get conversation history
history = agent.get_session_history("user_123")

# Clear session history
agent.clear_session("user_123")

# Delete session
agent.delete_session("user_123")
```

### Schema Exploration

```python
# Get basic schema
schema = agent.get_schema()

# Get detailed schema with relationships
schema_info = agent.get_schema_info(include_foreign_keys=True)
print(f"Total tables: {schema_info['total_tables']}")
print(f"Relationships: {len(schema_info['relationships'])}")
```

### Statistics and Monitoring

```python
# Get comprehensive statistics
stats = agent.get_stats()

print(f"Total queries: {stats['total_queries']}")
print(f"Cache hit rate: {stats['cache_hits'] / stats['total_queries'] * 100:.1f}%")
print(f"Active connections: {stats['pool']['checked_out']}")
print(f"Total sessions: {stats['sessions']['total_sessions']}")
```

## 🎯 Framework Integration

### Django

```python
# views.py
from django.conf import settings
from db_query_agent import DatabaseQueryAgent

agent = DatabaseQueryAgent(
    database_url=settings.DATABASES['default']['URL'],
    openai_api_key=settings.OPENAI_API_KEY
)

def query_database(request):
    question = request.POST.get('question')
    result = agent.query(question)
    return JsonResponse(result)
```

### FastAPI

```python
# main.py
from fastapi import FastAPI
from db_query_agent import DatabaseQueryAgent

app = FastAPI()
agent = DatabaseQueryAgent(database_url=os.getenv("DATABASE_URL"))

@app.post("/query")
async def query_db(question: str):
    return agent.query(question)
```

### Flask

```python
# app.py
from flask import Flask, request
from db_query_agent import DatabaseQueryAgent

app = Flask(__name__)
agent = DatabaseQueryAgent(database_url=os.getenv("DATABASE_URL"))

@app.route('/query', methods=['POST'])
def query():
    return agent.query(request.json['question'])
```

## ⚙️ Configuration

### Environment Variables (Recommended)

Create a `.env` file with all configuration:

```bash
# Required
OPENAI_API_KEY=sk-your-api-key
DATABASE_URL=postgresql://user:pass@localhost/db

# Model Configuration
MODEL_STRATEGY=adaptive
FAST_MODEL=gpt-4o-mini
BALANCED_MODEL=gpt-4.1-mini
COMPLEX_MODEL=gpt-4.1

# Cache Configuration
CACHE_ENABLED=true
CACHE_BACKEND=memory
CACHE_SCHEMA_TTL=3600
CACHE_QUERY_TTL=300
CACHE_LLM_TTL=3600

# Safety Configuration
READ_ONLY=true
QUERY_TIMEOUT=30
MAX_RESULT_ROWS=10000

# Connection Configuration
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Performance Configuration
LAZY_SCHEMA_LOADING=true
ENABLE_STREAMING=true
WARMUP_ON_INIT=false
```

Then load with a single line:
```python
agent = DatabaseQueryAgent.from_env()
```

### Direct Configuration

Pass parameters directly (overrides .env):

```python
from db_query_agent import DatabaseQueryAgent

agent = DatabaseQueryAgent(
    database_url="postgresql://...",
    openai_api_key="sk-...",
    
    # Model configuration
    model_strategy="adaptive",  # Use fast model for simple queries
    fast_model="gpt-4o-mini",   # 2s generation time
    balanced_model="gpt-4.1-mini",  # 3s generation time
    complex_model="gpt-4.1",     # 5s generation time
    
    # Cache configuration
    enable_cache=True,
    cache_backend="redis",
    schema_cache_ttl=3600,  # 1 hour
    query_cache_ttl=300,    # 5 minutes
    llm_cache_ttl=3600,     # 1 hour
    
    # Safety configuration
    read_only=True,
    allowed_tables=["users", "orders", "products"],
    blocked_tables=["sensitive_data"],
    max_query_timeout=30,
    max_result_rows=10000,
    
    # Connection configuration
    pool_size=10,
    max_overflow=20,
    
    # Performance configuration
    lazy_schema_loading=True,
    max_tables_in_context=5,
    enable_streaming=True,
    warmup_on_init=False,
    
    # Statistics configuration
    enable_statistics=True,  # Track queries, cache hits, etc.
    
    # Session configuration
    session_backend="sqlite",
    session_db_path="./sessions.db"
)
```

### Mixed Configuration

Load from `.env` and override specific values:

```python
# Load most settings from .env, override specific ones
agent = DatabaseQueryAgent.from_env(
    fast_model="gpt-4.1",  # Override model
    read_only=False,       # Override safety
    enable_statistics=True  # Add statistics
)
```

## 📊 Performance

With all optimizations enabled:

| Scenario | Response Time | Cache Hit |
|----------|---------------|-----------|
| Simple query (cached) | **0.5s** | ✅ |
| Simple query (uncached) | **1.5s** | ❌ |
| Complex query (cached) | **2s** | ✅ |
| Complex query (uncached) | **5s** | ❌ |

- **90% of queries** complete in < 3 seconds
- **First token** appears in < 500ms with streaming
- **Cache hit rate** typically > 60% in production

## 🔒 Security Features

- ✅ **Read-only mode** by default (only SELECT queries)
- ✅ **SQL injection prevention** with query parsing and validation
- ✅ **Table access control** with allowlist/blocklist
- ✅ **Query timeout** enforcement
- ✅ **Dangerous keyword detection** (DROP, DELETE, etc.)
- ✅ **Input/output guardrails** with OpenAI Agents SDK

## 📚 Documentation

### Core Documentation
- **[API Reference](./docs/API_REFERENCE.md)** - Complete API documentation for all classes and methods
- **[Integration Guides](./docs/INTEGRATION_GUIDES.md)** - Django, Flask, FastAPI, Streamlit, Jupyter integrations
- **[Troubleshooting Guide](./docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Architecture](./docs/ARCHITECTURE.md)** - System design and architecture decisions

### Examples
- **[Basic Examples](./examples/basic_usage.py)** - 7 basic usage examples
- **[Advanced Examples](./examples/advanced_usage.py)** - 8 advanced patterns and optimizations
- **[Examples Guide](./examples/README.md)** - Overview of all examples

## 🧪 Development

### Setup

```bash
# Clone repository
git clone https://github.com/Ocolus1/db-query-agent
cd db-query-agent

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run demo UI
streamlit run demo/streamlit_app.py
```

### Learn More

- **New to the package?** Start with [Basic Examples](./examples/basic_usage.py)
- **Integrating with a framework?** Check [Integration Guides](./docs/INTEGRATION_GUIDES.md)
- **Need help?** See [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
- **Want to understand the internals?** Read [Architecture](./docs/ARCHITECTURE.md)

## 📁 Project Structure

```
db-query-agent/
├── src/db_query_agent/          # Main package source code
│   ├── __init__.py
│   ├── agent.py                 # DatabaseQueryAgent - main interface
│   ├── simple_multi_agent_system.py  # Multi-agent orchestration
│   ├── agents/                  # Agent implementations
│   ├── tools/                   # Agent tools
│   ├── schema_extractor.py      # Database schema introspection
│   ├── cache_manager.py         # Multi-layer caching system
│   ├── connection_manager.py    # Database connection pooling
│   ├── query_validator.py       # SQL validation and safety
│   ├── session_manager.py       # Conversation session management
│   ├── config.py                # Configuration classes
│   └── exceptions.py            # Custom exceptions
│
├── docs/                        # Documentation
│   ├── API_REFERENCE.md         # Complete API documentation
│   ├── INTEGRATION_GUIDES.md    # Framework integration guides
│   ├── TROUBLESHOOTING.md       # Common issues & solutions
│   └── ARCHITECTURE.md          # System architecture
│
├── examples/                    # Usage examples
│   ├── basic_usage.py           # 7 basic examples
│   ├── advanced_usage.py        # 8 advanced examples
│   └── README.md                # Examples documentation
│
├── demo/                        # Demo application
│   ├── streamlit_app.py         # Interactive demo UI
│   └── create_demo_db.py        # Demo database setup
│
├── tests/                       # Test suite (133 tests)
│   ├── test_agent_integration.py
│   ├── test_cache_manager.py
│   ├── test_dynamic_configuration.py
│   ├── test_streaming.py
│   └── ...
│
└── pyproject.toml               # Package configuration
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue with details about the problem
2. **Suggest features** - Share your ideas for improvements
3. **Submit PRs** - Fix bugs or add features
4. **Improve docs** - Help make the documentation better
5. **Share feedback** - Let us know how you're using the package

Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- Database abstraction by [SQLAlchemy](https://www.sqlalchemy.org/)
- SQL parsing by [sqlparse](https://github.com/andialbrecht/sqlparse)

## 📧 Support

- 📖 [Documentation](https://github.com/Ocolus1/db-query-agent#readme)
- 🐛 [Issue Tracker](https://github.com/Ocolus1/db-query-agent/issues)
- 💬 [Discussions](https://github.com/Ocolus1/db-query-agent/discussions)

---

**Made with ❤️ for developers who want to query databases with natural language**
