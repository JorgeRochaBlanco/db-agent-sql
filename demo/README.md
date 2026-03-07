# 🤖 DB Query Agent - Streamlit Demo

Interactive demo application for the `db-query-agent` package.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From the project root
uv pip install -e ".[dev]"
```

### 2. Set Up Environment

**Important:** Create a `.env` file in the demo directory (credentials are read from here, not the UI):

```bash
# demo/.env
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite:///./demo_database.db
```

**Note:** The demo app reads credentials from the `.env` file for security. You won't enter them in the UI.

### 3. Create Demo Database (Optional)

```bash
python demo/create_demo_db.py
```

This creates a SQLite database with sample data (users, orders, products).

### 4. Run the Demo

```bash
streamlit run demo/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## ✨ Features

### 💬 Natural Language Query Interface
- Ask questions in plain English
- Get SQL queries automatically generated
- View results in tables
- Download results as CSV

### 📚 Schema Browser
- Explore database tables
- View column types and constraints
- See foreign key relationships
- Check indexes

### 📊 Visualizations
- Automatic chart generation
- Bar, line, and area charts
- Interactive data exploration

### 🕒 Query History
- Track all your queries
- Review past results
- Reuse successful queries

### 💬 Session Support
- Maintain conversation context
- Ask follow-up questions
- Reference previous queries

### 📈 Statistics Dashboard
- Total queries executed
- Cache hit rate
- Success/failure metrics
- Performance stats

---

## 🎯 Example Queries

Try these natural language questions:

```
How many users do we have?
Show me the top 10 products by revenue
What's the average order value?
List all active customers
Find orders over $1000
Which users have never placed an order?
What are the most popular product categories?
Show me monthly revenue trends
```

---

## 🔧 Configuration Options

### Database Connection

Supports multiple database types:

```bash
# SQLite
DATABASE_URL=sqlite:///./database.db

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/dbname

# SQL Server
DATABASE_URL=mssql+pyodbc://user:pass@localhost/dbname?driver=ODBC+Driver+17+for+SQL+Server
```

### Advanced Options

- **Read-Only Mode**: Prevents data modification (recommended)
- **Caching**: Speeds up repeated queries
- **Model Strategy**: 
  - `adaptive`: Automatically choose model based on complexity
  - `fixed`: Use same model for all queries

---

## 🔒 Security

### Best Practices

1. **Use Read-Only Mode** (enabled by default)
2. **Use Read-Only Database User**
3. **Don't commit API keys** (use `.env` file)
4. **Restrict table access** if needed
5. **Enable SSL** for remote databases

### Safe by Default

- All queries validated before execution
- Dangerous keywords blocked (DROP, DELETE, etc.)
- Read-only mode prevents modifications
- SSL/TLS support for secure connections

---

## 📸 Screenshots

### Main Query Interface
![Query Interface](./screenshots/query_interface.png)

### Schema Browser
![Schema Browser](./screenshots/schema_browser.png)

### Results Visualization
![Visualization](./screenshots/visualization.png)

---

## 🐛 Troubleshooting

### Connection Issues

**Problem**: "Connection failed"
- Check database URL format
- Verify database is running
- Check network connectivity
- Verify credentials

**Problem**: "SSL connection failed"
- Add `?sslmode=disable` for local databases
- Check SSL certificate paths
- See [SSL_CONFIGURATION.md](../SSL_CONFIGURATION.md)

### Query Issues

**Problem**: "Query validation failed"
- Check if query is SELECT-only (read-only mode)
- Verify table names exist
- Check for dangerous keywords

**Problem**: "No results returned"
- Verify data exists in tables
- Check query logic
- Review generated SQL

### API Issues

**Problem**: "OpenAI API error"
- Verify API key is correct
- Check API key has credits
- Check network connectivity

---

## 🎨 Customization

### Modify UI Theme

Edit `streamlit_app.py` CSS section:

```python
st.markdown("""
<style>
    .main-header {
        color: #your-color;
    }
</style>
""", unsafe_allow_html=True)
```

### Add Custom Features

The demo is modular - add your own tabs or features:

```python
with st.tabs(["Query", "Schema", "History", "Your Feature"]):
    # Your custom code
    pass
```

---

## 📚 Learn More

- [Main README](../README.md)
- [API Documentation](../docs/API.md)
- [SSL Configuration](../SSL_CONFIGURATION.md)
- [Phase 3 Plan](../PHASE_3_PLAN.md)

---

## 🤝 Contributing

Found a bug or have a feature request? Open an issue!

---

## 📄 License

Same as the main package.
