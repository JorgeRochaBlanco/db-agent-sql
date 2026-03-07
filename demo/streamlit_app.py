"""Streamlit demo app for db-query-agent."""

import streamlit as st
import pandas as pd
import asyncio
import time
from datetime import datetime
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="DB Query Agent Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Chat Interface Styles */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1rem;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .ai-message {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 1rem;
    }
    
    .ai-bubble {
        background: #f0f2f6;
        color: #262730;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .ai-bubble-content {
        margin-bottom: 0.5rem;
    }
    
    .timestamp {
        font-size: 0.75rem;
        color: #888;
        margin-top: 0.25rem;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .confidence-high {
        background-color: #d4edda;
        color: #155724;
    }
    
    .confidence-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .confidence-low {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Input area at bottom */
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_session' not in st.session_state:
        st.session_state.current_session = None
    if 'schema_cache' not in st.session_state:
        st.session_state.schema_cache = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'use_session' not in st.session_state:
        st.session_state.use_session = False
    if 'use_streaming' not in st.session_state:
        st.session_state.use_streaming = False
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False


def connect_to_database(**kwargs) -> bool:
    """Connect to database and initialize agent using flexible configuration.
    
    The agent will load credentials from .env by default, with overrides from kwargs.
    """
    try:
        from db_query_agent import DatabaseQueryAgent
        
        # Use from_env() which loads from .env and allows overrides
        st.session_state.agent = DatabaseQueryAgent.from_env(
            enable_statistics=True,  # Enable query statistics
            **kwargs
        )
        
        # Test connection
        if st.session_state.agent.connection_manager.test_connection():
            st.session_state.connected = True
            
            # Load schema
            st.session_state.schema_cache = st.session_state.agent.get_schema()
            
            return True
        else:
            st.error("❌ Connection test failed")
            return False
            
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        logger.error(f"Connection error: {e}", exc_info=True)
        return False


def sidebar_config():
    """Render sidebar configuration."""
    st.sidebar.markdown("## 🔧 Configuration")
    
    # Get credentials from environment
    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Database Configuration
    with st.sidebar.expander("🗄️ Database Connection", expanded=not st.session_state.connected):
        # Display connection info (masked)
        if database_url:
            # Mask sensitive parts of URL
            display_url = database_url
            if "://" in display_url and "@" in display_url:
                # Mask password in URL
                parts = display_url.split("://")
                if len(parts) == 2 and "@" in parts[1]:
                    auth_and_host = parts[1].split("@")
                    if ":" in auth_and_host[0]:
                        user = auth_and_host[0].split(":")[0]
                        display_url = f"{parts[0]}://{user}:****@{auth_and_host[1]}"
            
            st.info(f"📍 **Database:** `{display_url}`")
        else:
            st.error("❌ DATABASE_URL not found in .env file")
        
        if openai_api_key:
            st.info(f"🔑 **API Key:** `{openai_api_key[:8]}...{openai_api_key[-4:]}`")
        else:
            st.error("❌ OPENAI_API_KEY not found in .env file")
        
        # Advanced options
        with st.expander("Advanced Options"):
            read_only = st.checkbox("Read-Only Mode", value=True, help="Only allow SELECT queries")
            enable_cache = st.checkbox("Enable Caching", value=True)
            model_strategy = st.selectbox(
                "Model Strategy",
                ["adaptive", "fixed"],
                help="Adaptive: Choose model based on query complexity"
            )
        
        if st.button("🔌 Connect", type="primary", width="stretch", disabled=not (database_url and openai_api_key)):
            if not database_url or not openai_api_key:
                st.error("❌ Please set DATABASE_URL and OPENAI_API_KEY in demo/.env file")
            else:
                with st.spinner("Connecting..."):
                    # Pass overrides to from_env() - credentials loaded from .env automatically
                    success = connect_to_database(
                        read_only=read_only,
                        enable_cache=enable_cache,
                        model_strategy=model_strategy
                    )
                    if success:
                        st.success("✅ Connected successfully!")
                        st.rerun()
        
        if st.session_state.connected:
            if st.button("🔌 Disconnect", width="stretch"):
                st.session_state.agent = None
                st.session_state.connected = False
                st.session_state.schema_cache = None
                st.rerun()
    
    # Statistics
    if st.session_state.connected and st.session_state.agent:
        with st.sidebar.expander("📊 Statistics", expanded=True):
            stats = st.session_state.agent.get_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", stats.get('total_queries', 0))
                st.metric("Cache Hits", stats.get('cache_hits', 0))
            with col2:
                st.metric("Successful", stats.get('successful_queries', 0))
                st.metric("Failed", stats.get('failed_queries', 0))
            
            if stats.get('total_queries', 0) > 0:
                hit_rate = (stats.get('cache_hits', 0) / stats['total_queries']) * 100
                st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")


def render_schema_browser():
    """Render schema browser."""
    if not st.session_state.connected or not st.session_state.schema_cache:
        st.info("ℹ️ Connect to a database to view schema")
        return
    
    st.markdown("### 📚 Database Schema")
    
    schema = st.session_state.schema_cache
    
    # Table selector
    table_names = list(schema.keys())
    selected_table = st.selectbox("Select Table", table_names)
    
    if selected_table:
        table_info = schema[selected_table]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"#### 📋 {selected_table}")
            
            # Columns
            if 'columns' in table_info:
                columns_df = pd.DataFrame([
                    {
                        'Column': col['name'],
                        'Type': col['type'],
                        'Nullable': '✓' if col.get('nullable', True) else '✗',
                        'Primary Key': '✓' if col.get('primary_key', False) else '',
                    }
                    for col in table_info['columns']
                ])
                st.dataframe(columns_df, width="stretch", hide_index=True)
        
        with col2:
            # Table stats
            st.markdown("#### 📊 Table Info")
            st.metric("Columns", len(table_info.get('columns', [])))
            
            if 'foreign_keys' in table_info and table_info['foreign_keys']:
                st.metric("Foreign Keys", len(table_info['foreign_keys']))
            
            if 'indexes' in table_info and table_info['indexes']:
                st.metric("Indexes", len(table_info['indexes']))
        
        # Foreign Keys
        if 'foreign_keys' in table_info and table_info['foreign_keys']:
            with st.expander("🔗 Foreign Keys"):
                for fk in table_info['foreign_keys']:
                    st.markdown(f"- `{fk.get('constrained_columns', [])}` → `{fk.get('referred_table')}.{fk.get('referred_columns', [])}`")


# Note: Casual conversation and natural response generation
# is now handled by the agent itself (conversational_layer.py)
# No need to duplicate logic here!


def render_chat_message(message: dict, idx: int):
    """Render a single chat message bubble."""
    if message['type'] == 'thinking':
        # Show thinking indicator
        st.markdown(
            '<div style="text-align: left; margin: 10px 0;">'
            '<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'color: white; padding: 12px 20px; border-radius: 20px; display: inline-block; '
            'font-size: 14px;">🤔 Thinking...</span>'
            '</div>',
            unsafe_allow_html=True
        )
    elif message['type'] == 'user':
        # User message bubble
        st.markdown(f"""
        <div class="user-message">
            <div class="user-bubble">
                {message['content']}
                <div class="timestamp">{message['timestamp'].strftime('%I:%M %p')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # AI message bubble
        result = message['result']
        is_casual = result.get('is_casual', False)
        
        # Natural response is now generated by the agent's conversational layer
        natural_response = result.get('natural_response', 'I executed your query.')
        
        # Display AI bubble with natural response
        st.markdown(f"""
        <div class="ai-message">
            <div class="ai-bubble">
                <div class="ai-bubble-content">
                    {natural_response}
                </div>
                <div class="timestamp">{message['timestamp'].strftime('%I:%M %p')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Only show technical details for database queries, not casual conversation
        if is_casual:
            return
        
        # Confidence badge
        if 'confidence' in result:
            confidence = result['confidence']
            if confidence > 0.8:
                badge_class = "confidence-high"
                badge_text = f"✓ {confidence:.0%} confident"
            elif confidence > 0.5:
                badge_class = "confidence-medium"
                badge_text = f"⚠ {confidence:.0%} confident"
            else:
                badge_class = "confidence-low"
                badge_text = f"⚠ {confidence:.0%} confident"
            
            st.markdown(f'<span class="confidence-badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)


def render_query_interface():
    """Render chat-style query interface."""
    if not st.session_state.connected:
        st.info("ℹ️ Connect to a database to start querying")
        return
    
    st.markdown("### 💬 Chat with Your Database")
    
    # Session and Streaming toggles
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        st.session_state.use_session = st.checkbox("💬 Session", value=st.session_state.use_session, help="Maintain conversation context")
    with col3:
        # Streaming toggle - always visible, controls whether to use streaming
        st.session_state.use_streaming = st.checkbox("⚡ Stream", value=st.session_state.use_streaming, help="Stream responses token-by-token")
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display all chat messages
        for idx, message in enumerate(st.session_state.chat_messages):
            render_chat_message(message, idx)
    
    # Input area at bottom
    st.markdown("---")
    
    # Query input
    col1, col2 = st.columns([6, 1])
    with col1:
        query = st.text_input(
            "Type your question...",
            placeholder="e.g., How many users do we have?",
            label_visibility="collapsed",
            key="query_input",
            disabled=st.session_state.is_processing
        )
    with col2:
        send_button = st.button(
            "📤 Send", 
            type="primary", 
            width="stretch",
            disabled=st.session_state.is_processing or not query
        )
    
    # Handle query submission
    if send_button and query:
        # Set processing state
        st.session_state.is_processing = True
        
        # Add user message
        st.session_state.chat_messages.append({
            'type': 'user',
            'content': query,
            'timestamp': datetime.now()
        })
        
        # Execute query - agent handles casual conversation automatically
        try:
            # Determine session
            session_obj = None
            if st.session_state.use_session:
                if not st.session_state.current_session:
                    st.session_state.current_session = st.session_state.agent.create_session(
                        f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                session_obj = st.session_state.current_session.session
            
            # Use streaming if user toggled it on
            if st.session_state.use_streaming:
                # Create a placeholder for streaming text in the chat area
                streaming_placeholder = st.empty()
                
                # Stream the response with real-time display
                streamed_text = ""
                
                async def stream_response():
                    nonlocal streamed_text
                    async for chunk in st.session_state.agent.query_stream(query, session=session_obj):
                        streamed_text += chunk
                        # Display accumulated text in real-time
                        streaming_placeholder.markdown(
                            f'<div style="text-align: left; margin: 10px 0;">'
                            f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                            f'color: white; padding: 15px 20px; border-radius: 20px; display: inline-block; '
                            f'max-width: 70%; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">'
                            f'{streamed_text}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                        # Add artificial delay to slow down streaming (adjust as needed)
                        await asyncio.sleep(0.03)  # 30ms delay per token
                    return streamed_text
                
                # Run streaming (statistics are tracked at agent level)
                final_response = asyncio.run(stream_response())
                
                # Clear the streaming placeholder
                streaming_placeholder.empty()
                
                # Create result dict
                result = {
                    "natural_response": final_response,
                    "final_output": final_response
                }
            else:
                # Non-streaming query
                with st.spinner("🤔 Thinking..."):
                    result = asyncio.run(st.session_state.agent.query(query, session=session_obj))
            
            # Add AI response
            st.session_state.chat_messages.append({
                'type': 'ai',
                'result': result,
                'timestamp': datetime.now()
            })
            
            # Store in history (only if not casual)
            if not result.get('is_casual', False):
                st.session_state.query_history.insert(0, {
                    'timestamp': datetime.now(),
                    'question': query,
                    'result': result
                })
                
            # Reset processing state
            st.session_state.is_processing = False
            
            # Rerun to show new messages
            st.rerun()
            
        except Exception as e:
            st.session_state.is_processing = False
            st.error(f"❌ Error: {str(e)}")
            logger.error(f"Query error: {e}", exc_info=True)
    
    # Clear chat button
    if len(st.session_state.chat_messages) > 0:
        if st.button("🗑️ Clear Chat", disabled=st.session_state.is_processing):
            st.session_state.chat_messages = []
            st.session_state.is_processing = False
            st.rerun()


def display_query_result(result: dict):
    """Display query result."""
    st.markdown("---")
    st.markdown("### 📊 Results")
    
    # SQL Query
    with st.expander("🔍 Generated SQL", expanded=True):
        st.code(result.get('sql', 'N/A'), language='sql')
    
    # Explanation
    if 'explanation' in result:
        with st.expander("💡 Explanation"):
            st.markdown(result['explanation'])
    
    # Confidence
    if 'confidence' in result:
        confidence = result['confidence']
        color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
        st.markdown(f"**Confidence:** :{color}[{confidence:.1%}]")
    
    # Results data
    if 'results' in result and result['results']:
        st.markdown("#### 📋 Data")
        
        # Convert to DataFrame
        results_data = result['results']
        if results_data:
            # Get column names from first row or use generic names
            if hasattr(results_data[0], '_fields'):
                columns = results_data[0]._fields
            else:
                columns = [f"col_{i}" for i in range(len(results_data[0]))]
            
            df = pd.DataFrame(results_data, columns=columns)
            
            # Display table
            st.dataframe(df, width="stretch")
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Visualization options
            if len(df) > 0 and len(df.columns) > 0:
                with st.expander("📈 Visualize"):
                    chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Area Chart"])
                    
                    # Select columns for visualization
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    
                    if numeric_cols:
                        y_col = st.selectbox("Y-axis", numeric_cols)
                        x_col = st.selectbox("X-axis (optional)", ["Index"] + df.columns.tolist())
                        
                        if x_col == "Index":
                            chart_data = df[[y_col]]
                        else:
                            chart_data = df.set_index(x_col)[[y_col]]
                        
                        if chart_type == "Bar Chart":
                            st.bar_chart(chart_data)
                        elif chart_type == "Line Chart":
                            st.line_chart(chart_data)
                        elif chart_type == "Area Chart":
                            st.area_chart(chart_data)
    
    # Natural language response
    if 'natural_response' in result:
        st.markdown("#### 💬 Answer")
        st.info(result['natural_response'])


def render_query_history():
    """Render query history."""
    if not st.session_state.query_history:
        st.info("ℹ️ No queries yet. Start asking questions!")
        return
    
    st.markdown("### 🕒 Query History")
    
    for idx, item in enumerate(st.session_state.query_history[:10]):  # Show last 10
        with st.expander(f"**{item['question'][:50]}...** - {item['timestamp'].strftime('%H:%M:%S')}"):
            st.markdown(f"**Question:** {item['question']}")
            
            # Show agent's natural response
            natural_response = item['result'].get('natural_response', 'No response available')
            st.markdown(f"**Answer:** {natural_response}")
            
            # Show execution time if available
            if 'execution_time' in item['result']:
                st.caption(f"⚡ Executed in {item['result']['execution_time']:.2f}s")


def main():
    """Main application."""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 DB Query Agent Demo</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Natural Language Database Queries with AI</div>', unsafe_allow_html=True)
    
    # Sidebar
    sidebar_config()
    
    # Main content
    if st.session_state.connected:
        # Tabs
        tab1, tab2, tab3 = st.tabs(["💬 Query", "📚 Schema", "🕒 History"])
        
        with tab1:
            render_query_interface()
        
        with tab2:
            render_schema_browser()
        
        with tab3:
            render_query_history()
    else:
        # Welcome screen
        st.markdown("""
        ## 👋 Welcome!
        
        This demo showcases the **db-query-agent** package - an AI-powered natural language interface for databases.
        
        ### 🚀 Getting Started
        
        1. **Create** a `demo/.env` file with your credentials:
           ```
           DATABASE_URL=sqlite:///./demo_database.db
           OPENAI_API_KEY=sk-your-key-here
           ```
        2. **Click** Connect in the sidebar
        3. **Start** asking questions in natural language!
        
        ### ✨ Features
        
        - 🤖 **Natural Language Queries** - Ask questions in plain English
        - 🔒 **Read-Only Mode** - Safe querying without data modification
        - 💾 **Smart Caching** - Fast repeated queries
        - 📊 **Schema Browser** - Explore your database structure
        - 📈 **Visualizations** - Automatic chart generation
        - 🕒 **Query History** - Track your queries
        - 💬 **Session Support** - Conversational context
        
        ### 📚 Example Questions
        
        - "How many users do we have?"
        - "Show me the top 10 products by revenue"
        - "What's the average order value this month?"
        - "List all active customers"
        - "Find orders over $1000"
        
        ### 🔐 Security
        
        - All queries are validated before execution
        - Read-only mode prevents data modification
        - SSL/TLS support for secure connections
        - No data is stored or transmitted outside your environment
        """)
        
        # Quick start example
        with st.expander("🎯 Quick Start - Create demo/.env"):
            st.markdown("**1. Create the file:**")
            st.code("demo/.env", language="bash")
            
            st.markdown("**2. Add your credentials:**")
            st.code("""DATABASE_URL=sqlite:///./demo_database.db
OPENAI_API_KEY=sk-your-key-here""", language="bash")
            
            st.markdown("**3. Restart the app and click Connect!**")


if __name__ == "__main__":
    main()
