# Examples

Complete examples demonstrating `db-query-agent` usage.

---

## Basic Examples

### `basic_usage.py`

Demonstrates fundamental features:

1. **Simple Query** - Basic query with direct configuration
2. **Environment Configuration** - Load from `.env` file
3. **Streaming** - Token-by-token responses
4. **Sessions** - Multi-turn conversations
5. **Schema Exploration** - Explore database structure
6. **Error Handling** - Handle errors gracefully
7. **Custom Configuration** - Advanced configuration options

**Run:**
```bash
python examples/basic_usage.py
```

---

## Advanced Examples

### `advanced_usage.py`

Demonstrates advanced patterns:

1. **Batch Queries** - Execute multiple queries efficiently
2. **Concurrent Queries** - Parallel query execution
3. **Streaming with Processing** - Process streaming responses
4. **Session Management** - Advanced session handling
5. **Caching Strategies** - Optimize with caching
6. **Error Recovery** - Robust error handling
7. **Custom Workflow** - Multiple specialized agents
8. **Performance Monitoring** - Track and optimize performance

**Run:**
```bash
python examples/advanced_usage.py
```

---

## Framework Integration Examples

See [Integration Guides](../docs/INTEGRATION_GUIDES.md) for:

- Django integration
- Flask integration
- FastAPI integration
- Streamlit integration
- Jupyter Notebook integration

---

## Prerequisites

1. **Install package:**
```bash
pip install db-query-agent
```

2. **Set up environment:**
```bash
# Copy example .env
cp .env.example .env

# Edit .env with your credentials
DATABASE_URL=postgresql://user:pass@localhost/db
OPENAI_API_KEY=sk-your-key-here
```

3. **Create demo database (optional):**
```bash
python demo/create_demo_db.py
```

---

## Example Output

### Basic Query
```
Question: How many users do we have?
Answer: You have 150 users in your database.
SQL: SELECT COUNT(*) FROM users
```

### Streaming Query
```
Question: How many orders do we have?
Answer: You have 1,234 orders in your database.
```
(Displayed token-by-token)

### Session Conversation
```
Q: How many users do we have?
A: You have 150 users in your database.

Q: Show me the active ones
A: There are 120 active users. Here are some details...

Q: Filter by users created this month
A: 15 users were created this month...
```

---

## Tips

### Performance

1. **Enable caching:**
```python
agent = DatabaseQueryAgent.from_env(enable_cache=True)
```

2. **Use concurrent queries:**
```python
tasks = [agent.query(q) for q in questions]
results = await asyncio.gather(*tasks)
```

3. **Monitor statistics:**
```python
stats = agent.get_stats()
print(f"Cache hit rate: {stats['cache_hits']/stats['total_queries']*100:.1f}%")
```

### Error Handling

```python
result = await agent.query("your question")
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Success: {result['natural_response']}")
```

### Sessions

```python
# Create session
session = agent.create_session("user_123")

# Use session
result = await session.ask("question")

# Cleanup
agent.delete_session("user_123")
```

---

## See Also

- [API Reference](../docs/API_REFERENCE.md)
- [Integration Guides](../docs/INTEGRATION_GUIDES.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)
- [Architecture](../docs/ARCHITECTURE.md)
