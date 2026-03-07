# Integration Guides

Step-by-step guides for integrating `db-query-agent` with popular Python frameworks.

---

## Table of Contents

- [Django Integration](#django-integration)
- [Flask Integration](#flask-integration)
- [FastAPI Integration](#fastapi-integration)
- [Streamlit Integration](#streamlit-integration)
- [Jupyter Notebook Integration](#jupyter-notebook-integration)

---

## Django Integration

### Setup

1. **Install the package:**

```bash
pip install db-query-agent
```

2. **Add to Django settings:**

```python
# settings.py

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'db_query_agent',
]

# Database Query Agent Configuration
DB_QUERY_AGENT = {
    'DATABASE_URL': 'postgresql://user:pass@localhost/mydb',
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'ENABLE_CACHE': True,
    'READ_ONLY': True,
    'ENABLE_STREAMING': True,
}
```

3. **Create agent service:**

```python
# myapp/services/query_agent.py

from db_query_agent import DatabaseQueryAgent
from django.conf import settings

class QueryAgentService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern for agent instance."""
        if cls._instance is None:
            config = settings.DB_QUERY_AGENT
            cls._instance = DatabaseQueryAgent(
                database_url=config['DATABASE_URL'],
                openai_api_key=config['OPENAI_API_KEY'],
                enable_cache=config.get('ENABLE_CACHE', True),
                read_only=config.get('READ_ONLY', True),
                enable_streaming=config.get('ENABLE_STREAMING', False),
            )
        return cls._instance
    
    @classmethod
    def close(cls):
        """Close agent connection."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
```

4. **Create views:**

```python
# myapp/views.py

from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from asgiref.sync import async_to_sync
import asyncio
import json
from .services.query_agent import QueryAgentService

class QueryView(View):
    """Handle natural language queries."""
    
    def post(self, request):
        data = json.loads(request.body)
        question = data.get('question')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        # Get agent instance
        agent = QueryAgentService.get_instance()
        
        # Execute query
        result = async_to_sync(agent.query)(question)
        
        return JsonResponse(result)


class StreamingQueryView(View):
    """Handle streaming queries."""
    
    def post(self, request):
        data = json.loads(request.body)
        question = data.get('question')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        # Get agent instance
        agent = QueryAgentService.get_instance()
        
        # Stream response
        async def stream_generator():
            async for chunk in agent.query_stream(question):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Convert async generator to sync
        def sync_generator():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = stream_generator()
                while True:
                    try:
                        chunk = loop.run_until_complete(async_gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()
        
        return StreamingHttpResponse(
            sync_generator(),
            content_type='text/event-stream'
        )


class SessionQueryView(View):
    """Handle session-based queries."""
    
    def post(self, request):
        data = json.loads(request.body)
        question = data.get('question')
        session_id = data.get('session_id', request.session.session_key)
        
        # Get agent instance
        agent = QueryAgentService.get_instance()
        
        # Create or get session
        chat_session = agent.create_session(session_id)
        
        # Execute query with session
        result = async_to_sync(chat_session.ask)(question)
        
        return JsonResponse(result)
```

5. **Add URLs:**

```python
# myapp/urls.py

from django.urls import path
from .views import QueryView, StreamingQueryView, SessionQueryView

urlpatterns = [
    path('api/query/', QueryView.as_view(), name='query'),
    path('api/query/stream/', StreamingQueryView.as_view(), name='query_stream'),
    path('api/query/session/', SessionQueryView.as_view(), name='query_session'),
]
```

6. **Frontend example:**

```javascript
// Simple query
fetch('/api/query/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: 'How many users?'})
})
.then(response => response.json())
.then(data => console.log(data.natural_response));

// Streaming query
const eventSource = new EventSource('/api/query/stream/');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.chunk);
};

// Session-based query
fetch('/api/query/session/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        question: 'Show me active users',
        session_id: 'user_123'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Flask Integration

### Setup

1. **Install the package:**

```bash
pip install db-query-agent flask
```

2. **Create Flask app:**

```python
# app.py

from flask import Flask, request, jsonify, Response, stream_with_context
from db_query_agent import DatabaseQueryAgent
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize agent
agent = DatabaseQueryAgent.from_env(
    enable_streaming=True,
    enable_statistics=True
)

# Store sessions
sessions = {}


@app.route('/api/query', methods=['POST'])
def query():
    """Handle natural language queries."""
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    # Execute query
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(agent.query(question))
    loop.close()
    
    return jsonify(result)


@app.route('/api/query/stream', methods=['POST'])
def query_stream():
    """Handle streaming queries."""
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def stream():
            async for chunk in agent.query_stream(question):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        async_gen = stream()
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
        
        loop.close()
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )


@app.route('/api/query/session', methods=['POST'])
def query_session():
    """Handle session-based queries."""
    data = request.get_json()
    question = data.get('question')
    session_id = data.get('session_id', 'default')
    
    # Create or get session
    if session_id not in sessions:
        sessions[session_id] = agent.create_session(session_id)
    
    chat_session = sessions[session_id]
    
    # Execute query
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(chat_session.ask(question))
    loop.close()
    
    return jsonify(result)


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get agent statistics."""
    return jsonify(agent.get_stats())


@app.route('/api/schema', methods=['GET'])
def schema():
    """Get database schema."""
    include_fks = request.args.get('include_foreign_keys', 'true').lower() == 'true'
    return jsonify(agent.get_schema_info(include_foreign_keys=include_fks))


@app.teardown_appcontext
def shutdown_agent(exception=None):
    """Close agent on shutdown."""
    agent.close()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

3. **Frontend example:**

```javascript
// Simple query
fetch('/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: 'How many users?'})
})
.then(response => response.json())
.then(data => console.log(data.natural_response));

// Get statistics
fetch('/api/stats')
    .then(response => response.json())
    .then(stats => console.log(stats));
```

---

## FastAPI Integration

### Setup

1. **Install the package:**

```bash
pip install db-query-agent fastapi uvicorn
```

2. **Create FastAPI app:**

```python
# main.py

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from db_query_agent import DatabaseQueryAgent
from typing import Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DB Query Agent API")

# Initialize agent
agent = DatabaseQueryAgent.from_env(
    enable_streaming=True,
    enable_statistics=True
)

# Store sessions
sessions = {}


# Request models
class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    natural_response: str
    sql: Optional[str] = None
    results: Optional[list] = None
    execution_time: float


# Dependency
def get_agent():
    """Get agent instance."""
    return agent


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, agent: DatabaseQueryAgent = Depends(get_agent)):
    """Execute natural language query."""
    result = await agent.query(request.question)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.post("/api/query/stream")
async def query_stream(request: QueryRequest, agent: DatabaseQueryAgent = Depends(get_agent)):
    """Execute streaming query."""
    
    async def generate():
        async for chunk in agent.query_stream(request.question):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.post("/api/query/session", response_model=QueryResponse)
async def query_session(request: QueryRequest, agent: DatabaseQueryAgent = Depends(get_agent)):
    """Execute query with session context."""
    session_id = request.session_id or "default"
    
    # Create or get session
    if session_id not in sessions:
        sessions[session_id] = agent.create_session(session_id)
    
    chat_session = sessions[session_id]
    result = await chat_session.ask(request.question)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.get("/api/stats")
async def get_stats(agent: DatabaseQueryAgent = Depends(get_agent)):
    """Get agent statistics."""
    return agent.get_stats()


@app.get("/api/schema")
async def get_schema(
    include_foreign_keys: bool = True,
    agent: DatabaseQueryAgent = Depends(get_agent)
):
    """Get database schema."""
    return agent.get_schema_info(include_foreign_keys=include_foreign_keys)


@app.get("/api/sessions")
async def list_sessions(agent: DatabaseQueryAgent = Depends(get_agent)):
    """List all active sessions."""
    return {"sessions": agent.list_sessions()}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, agent: DatabaseQueryAgent = Depends(get_agent)):
    """Delete a session."""
    agent.delete_session(session_id)
    if session_id in sessions:
        del sessions[session_id]
    return {"message": f"Session {session_id} deleted"}


@app.on_event("shutdown")
async def shutdown():
    """Close agent on shutdown."""
    agent.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

3. **Run the server:**

```bash
uvicorn main:app --reload
```

4. **API documentation:**

Visit `http://localhost:8000/docs` for interactive API documentation.

5. **Client example:**

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/api/query",
    json={"question": "How many users?"}
)
print(response.json()["natural_response"])

# Session-based query
response = requests.post(
    "http://localhost:8000/api/query/session",
    json={
        "question": "Show active users",
        "session_id": "user_123"
    }
)
print(response.json())

# Get statistics
stats = requests.get("http://localhost:8000/api/stats").json()
print(stats)
```

---

## Streamlit Integration

### Setup

1. **Install the package:**

```bash
pip install db-query-agent streamlit
```

2. **Create Streamlit app:**

```python
# streamlit_app.py

import streamlit as st
import asyncio
from db_query_agent import DatabaseQueryAgent

# Page config
st.set_page_config(
    page_title="DB Query Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize agent
@st.cache_resource
def get_agent():
    return DatabaseQueryAgent.from_env(
        enable_streaming=True,
        enable_statistics=True
    )

agent = get_agent()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    use_streaming = st.checkbox("Enable Streaming", value=True)
    use_session = st.checkbox("Use Session", value=False)
    
    if st.button("Clear Cache"):
        st.cache_resource.clear()
        st.success("Cache cleared!")
    
    # Statistics
    st.markdown("### 📊 Statistics")
    stats = agent.get_stats()
    st.metric("Total Queries", stats.get("total_queries", 0))
    st.metric("Cache Hits", stats.get("cache_hits", 0))

# Main area
st.title("🤖 Database Query Agent")
st.markdown("Ask questions about your database in natural language")

# Query input
question = st.text_input(
    "Your question:",
    placeholder="e.g., How many users do we have?"
)

if st.button("Ask", type="primary"):
    if question:
        with st.spinner("Thinking..."):
            # Create session if needed
            session_obj = None
            if use_session:
                if 'session' not in st.session_state:
                    st.session_state.session = agent.create_session("streamlit_session")
                session_obj = st.session_state.session.session
            
            # Execute query
            if use_streaming:
                # Streaming response
                response_placeholder = st.empty()
                full_response = ""
                
                async def stream():
                    nonlocal full_response
                    async for chunk in agent.query_stream(question, session=session_obj):
                        full_response += chunk
                        response_placeholder.markdown(full_response)
                
                asyncio.run(stream())
            else:
                # Regular response
                result = asyncio.run(agent.query(question, session=session_obj))
                st.markdown(f"**Answer:** {result['natural_response']}")
                
                if result.get('sql'):
                    with st.expander("View SQL"):
                        st.code(result['sql'], language='sql')
                
                if result.get('results'):
                    with st.expander("View Results"):
                        st.json(result['results'])

# Schema browser
with st.expander("📚 Database Schema"):
    schema_info = agent.get_schema_info()
    st.write(f"**Total Tables:** {schema_info['total_tables']}")
    
    for table_name, table_info in schema_info['tables'].items():
        st.markdown(f"### {table_name}")
        st.write(f"Columns: {len(table_info['columns'])}")
        st.write(f"Primary Keys: {', '.join(table_info['primary_keys'])}")
```

3. **Run the app:**

```bash
streamlit run streamlit_app.py
```

---

## Jupyter Notebook Integration

### Setup

1. **Install the package:**

```bash
pip install db-query-agent jupyter
```

2. **Create notebook:**

```python
# Cell 1: Setup
from db_query_agent import DatabaseQueryAgent
import asyncio
from IPython.display import display, Markdown

# Initialize agent
agent = DatabaseQueryAgent.from_env(
    enable_statistics=True
)

print("✅ Agent initialized successfully!")
```

```python
# Cell 2: Simple query function
async def ask(question):
    """Helper function for queries."""
    result = await agent.query(question)
    
    # Display natural response
    display(Markdown(f"**Answer:** {result['natural_response']}"))
    
    # Display SQL
    if result.get('sql'):
        display(Markdown(f"**SQL:**\n```sql\n{result['sql']}\n```"))
    
    # Display results
    if result.get('results'):
        import pandas as pd
        df = pd.DataFrame(result['results'])
        display(df)
    
    return result

# Example usage
await ask("How many users do we have?")
```

```python
# Cell 3: Streaming query
async def ask_stream(question):
    """Helper function for streaming queries."""
    from IPython.display import clear_output
    
    full_response = ""
    async for chunk in agent.query_stream(question):
        full_response += chunk
        clear_output(wait=True)
        display(Markdown(full_response))
    
    return full_response

# Example usage
await ask_stream("Show me the top 10 products by price")
```

```python
# Cell 4: Session-based conversation
session = agent.create_session("notebook_session")

# First question
result1 = await session.ask("How many orders do we have?")
display(Markdown(result1['natural_response']))

# Follow-up question (remembers context)
result2 = await session.ask("Show me the recent ones")
display(Markdown(result2['natural_response']))
```

```python
# Cell 5: Explore schema
schema_info = agent.get_schema_info()

print(f"Total tables: {schema_info['total_tables']}")
print(f"Relationships: {len(schema_info['relationships'])}")

# Display tables
for table_name, table_info in schema_info['tables'].items():
    print(f"\n{table_name}:")
    print(f"  Columns: {len(table_info['columns'])}")
    print(f"  Primary Keys: {table_info['primary_keys']}")
```

```python
# Cell 6: Statistics
stats = agent.get_stats()

import pandas as pd
stats_df = pd.DataFrame([{
    'Total Queries': stats['total_queries'],
    'Successful': stats['successful_queries'],
    'Failed': stats['failed_queries'],
    'Cache Hits': stats['cache_hits'],
    'Cache Hit Rate': f"{(stats['cache_hits']/stats['total_queries']*100):.1f}%" if stats['total_queries'] > 0 else "0%"
}])

display(stats_df)
```

---

## See Also

- [API Reference](API_REFERENCE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Examples](../examples/)
