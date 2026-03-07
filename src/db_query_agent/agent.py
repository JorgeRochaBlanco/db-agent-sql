"""Main DatabaseQueryAgent class - the primary interface for the package."""

import logging
import time
import os
from typing import Dict, Any, Optional, AsyncIterator
from sqlalchemy import create_engine
from db_query_agent.config import AgentConfig, DatabaseConfig, CacheConfig, ModelConfig, SafetyConfig, get_env
from db_query_agent.schema_extractor import SchemaExtractor
from db_query_agent.cache_manager import CacheManager
from db_query_agent.connection_manager import ConnectionManager
from db_query_agent.query_validator import QueryValidator
from db_query_agent.agent_integration import DatabaseContext
from db_query_agent.session_manager import SessionManager, ChatSession
from db_query_agent.simple_multi_agent_system import SimpleMultiAgentSystem
from db_query_agent.exceptions import DatabaseQueryAgentError

logger = logging.getLogger(__name__)


class DatabaseQueryAgent:
    """
    Main interface for natural language database querying.
    
    This agent can be configured in two ways:
    1. Pass all parameters directly to constructor
    2. Load from .env file using from_env() class method
    
    Example 1 - Direct configuration:
        >>> agent = DatabaseQueryAgent(
        ...     database_url="postgresql://user:pass@localhost/db",
        ...     openai_api_key="sk-...",
        ...     fast_model="gpt-4o-mini",
        ...     enable_statistics=True
        ... )
        
    Example 2 - Load from .env:
        >>> agent = DatabaseQueryAgent.from_env(
        ...     read_only=True,
        ...     enable_statistics=True
        ... )
        
    Example 3 - Mixed (override .env):
        >>> agent = DatabaseQueryAgent.from_env(
        ...     database_url="postgresql://localhost/mydb",
        ...     fast_model="gpt-4.1"
        ... )
    """
    
    def __init__(
        self,
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
    ):
        """
        Initialize DatabaseQueryAgent.
        
        All parameters are optional. If not provided, they will be loaded from .env file.
        Parameters override .env values.
        
        Args:
            database_url: Database connection URL (from .env: DATABASE_URL)
            openai_api_key: OpenAI API key (from .env: OPENAI_API_KEY)
            model_strategy: Model selection strategy (from .env: MODEL_STRATEGY)
            fast_model: Fast model for simple queries (from .env: FAST_MODEL)
            balanced_model: Balanced model (from .env: BALANCED_MODEL)
            complex_model: Complex model (from .env: COMPLEX_MODEL)
            enable_cache: Enable caching (from .env: CACHE_ENABLED)
            cache_backend: Cache backend (from .env: CACHE_BACKEND)
            schema_cache_ttl: Schema cache TTL (from .env: CACHE_SCHEMA_TTL)
            query_cache_ttl: Query cache TTL (from .env: CACHE_QUERY_TTL)
            llm_cache_ttl: LLM cache TTL (from .env: CACHE_LLM_TTL)
            read_only: Only SELECT queries (from .env: READ_ONLY)
            allowed_tables: List of allowed tables
            blocked_tables: List of blocked tables
            max_query_timeout: Max query time (from .env: QUERY_TIMEOUT)
            max_result_rows: Max result rows (from .env: MAX_RESULT_ROWS)
            pool_size: Connection pool size (from .env: DB_POOL_SIZE)
            max_overflow: Max overflow connections (from .env: DB_MAX_OVERFLOW)
            lazy_schema_loading: Load only relevant tables (from .env: LAZY_SCHEMA_LOADING)
            max_tables_in_context: Max tables in context (from .env: MAX_TABLES_IN_CONTEXT)
            warmup_on_init: Warm up cache (from .env: WARMUP_ON_INIT)
            enable_statistics: Track query statistics
            enable_streaming: Enable streaming responses (from .env: ENABLE_STREAMING)
            session_backend: Session backend ('sqlite' or 'memory')
            session_db_path: Path to session database file
        """
        logger.info("Initializing DatabaseQueryAgent")
        
        # Get credentials (parameter > env > error)
        api_key = openai_api_key or get_env("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY must be provided as parameter or environment variable"
            )
        
        db_url = database_url or get_env("DATABASE_URL")
        if not db_url:
            raise ValueError(
                "DATABASE_URL must be provided as parameter or environment variable"
            )
        
        # Helper function to get value with fallback
        def get_config_value(param_value, env_key, default, value_type=str):
            if param_value is not None:
                return param_value
            env_value = get_env(env_key)
            if env_value is not None:
                if value_type == bool:
                    return env_value.lower() == "true"
                elif value_type == int:
                    return int(env_value)
                elif value_type == float:
                    return float(env_value)
                return env_value
            return default
        
        # Build configurations
        self.config = AgentConfig(
            openai_api_key=api_key,
            database=DatabaseConfig(
                url=db_url,
                pool_size=get_config_value(pool_size, "DB_POOL_SIZE", 10, int),
                max_overflow=get_config_value(max_overflow, "DB_MAX_OVERFLOW", 20, int)
            ),
            cache=CacheConfig(
                enabled=get_config_value(enable_cache, "CACHE_ENABLED", True, bool),
                backend=get_config_value(cache_backend, "CACHE_BACKEND", "memory"),
                schema_ttl=get_config_value(schema_cache_ttl, "CACHE_SCHEMA_TTL", 3600, int),
                query_ttl=get_config_value(query_cache_ttl, "CACHE_QUERY_TTL", 300, int),
                llm_ttl=get_config_value(llm_cache_ttl, "CACHE_LLM_TTL", 3600, int)
            ),
            model=ModelConfig(
                strategy=get_config_value(model_strategy, "MODEL_STRATEGY", "adaptive"),
                fast_model=get_config_value(fast_model, "FAST_MODEL", "gpt-4o-mini"),
                balanced_model=get_config_value(balanced_model, "BALANCED_MODEL", "gpt-4.1-mini"),
                complex_model=get_config_value(complex_model, "COMPLEX_MODEL", "gpt-4.1")
            ),
            safety=SafetyConfig(
                read_only=get_config_value(read_only, "READ_ONLY", True, bool),
                allowed_tables=allowed_tables,
                blocked_tables=blocked_tables,
                max_query_timeout=get_config_value(max_query_timeout, "QUERY_TIMEOUT", 30, int),
                max_result_rows=get_config_value(max_result_rows, "MAX_RESULT_ROWS", 10000, int)
            ),
            enable_streaming=get_config_value(enable_streaming, "ENABLE_STREAMING", True, bool),
            lazy_schema_loading=get_config_value(lazy_schema_loading, "LAZY_SCHEMA_LOADING", True, bool),
            max_tables_in_context=get_config_value(max_tables_in_context, "MAX_TABLES_IN_CONTEXT", 5, int),
            warmup_on_init=get_config_value(warmup_on_init, "WARMUP_ON_INIT", False, bool)
        )
        
        # Statistics configuration
        self.enable_statistics = enable_statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0,
        } if enable_statistics else None
        
        # Streaming configuration
        self.enable_streaming = get_config_value(enable_streaming, "ENABLE_STREAMING", False, bool)
        
        # Session configuration
        self.session_backend = session_backend or "sqlite"
        self.session_db_path = session_db_path
        
        # Initialize components
        self._initialize_components()
        
        # Warmup if requested
        if warmup_on_init:
            self._warmup()
        
        logger.info("DatabaseQueryAgent initialized successfully")
    
    def _initialize_components(self) -> None:
        """Initialize all components."""
        # Connection manager
        self.connection_manager = ConnectionManager(self.config.database)
        
        # Test connection
        if not self.connection_manager.test_connection():
            raise DatabaseQueryAgentError("Failed to connect to database")
        
        # Schema extractor
        self.schema_extractor = SchemaExtractor(
            self.connection_manager.engine,
            cache_ttl=self.config.cache.schema_ttl
        )
        
        # Cache manager
        self.cache_manager = CacheManager(
            schema_ttl=self.config.cache.schema_ttl,
            query_ttl=self.config.cache.query_ttl,
            llm_ttl=self.config.cache.llm_ttl
        )
        
        # Query validator
        self.query_validator = QueryValidator(
            read_only=self.config.safety.read_only,
            allowed_tables=self.config.safety.allowed_tables,
            blocked_tables=self.config.safety.blocked_tables
        )
        
        # Database context
        self.db_context = DatabaseContext(
            connection_manager=self.connection_manager,
            schema_extractor=self.schema_extractor,
            validator=self.query_validator,
            safety_config=self.config.safety
        )
        
        # Session manager
        self.session_manager = SessionManager(
            backend=self.session_backend,
            db_path=self.session_db_path
        )
        
        # Initialize multi-agent system (only system available)
        logger.info("Initializing multi-agent system (optimized for speed)...")
        self.multi_agent_system = SimpleMultiAgentSystem(
            database_context=self.db_context,
            model_config=self.config.model,
            openai_api_key=self.config.openai_api_key,
            cache_manager=self.cache_manager,
            cache_enabled=self.config.cache.enabled
        )
        logger.info("Multi-agent system initialized (1 LLM call per query)")
    
    def _warmup(self) -> None:
        """Warm up cache and connections."""
        logger.info("Warming up agent...")
        
        # Pre-load schema
        schema = self.schema_extractor.get_schema()
        logger.info(f"Schema loaded: {len(schema)} tables")
        
        # Test query
        try:
            self.connection_manager.execute_query("SELECT 1")
            logger.info("Connection pool warmed up")
        except Exception as e:
            logger.warning(f"Warmup query failed: {e}")
    
    async def query(
        self,
        question: str,
        return_sql: bool = True,
        return_results: bool = True,
        return_natural_response: bool = True,
        session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Query database using natural language.
        
        Args:
            question: Natural language question
            return_sql: Include SQL in response
            return_results: Execute query and return results
            return_natural_response: Generate natural language response
            
        Returns:
            Dictionary with query results
        """
        start_time = time.time()
        logger.info(f"Processing query: {question}")
        
        try:
            # Use multi-agent system (only system available)
            logger.info("Using multi-agent system (conversational-first)")
            
            # Check if this will be a cache hit (for stats)
            was_cached = False
            if self.config.cache.enabled:
                schema_hash = str(hash(str(self.schema_extractor.get_schema())))
                cached = self.cache_manager.get_llm_response(question, schema_hash)
                was_cached = cached is not None
            
            result = await self.multi_agent_system.query(question, session=session)
            result["execution_time"] = time.time() - start_time
            
            # Update statistics
            if self.enable_statistics and not result.get('is_casual', False):
                self.stats["total_queries"] += 1
                if was_cached:
                    self.stats["cache_hits"] += 1
                if result.get('error'):
                    self.stats["failed_queries"] += 1
                else:
                    self.stats["successful_queries"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            # Update failure stats
            if self.enable_statistics:
                self.stats["failed_queries"] += 1
            return {
                "question": question,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    async def query_stream(
        self,
        question: str,
        session: Optional[Any] = None
    ) -> AsyncIterator[str]:
        """
        Query database with streaming response (token-by-token).
        
        This provides a better user experience by showing responses as they're generated,
        reducing perceived wait time.
        
        Args:
            question: Natural language question
            session: Optional session for conversation history
            
        Yields:
            Response tokens as they are generated
        """
        logger.info(f"Processing streaming query: {question}")
        
        # Check if this will be a cache hit (for stats)
        was_cached = False
        if self.config.cache.enabled:
            schema_hash = str(hash(str(self.schema_extractor.get_schema())))
            cached = self.cache_manager.get_llm_response(question, schema_hash)
            was_cached = cached is not None
        
        try:
            # Use multi-agent system streaming
            has_error = False
            async for chunk in self.multi_agent_system.query_stream(question, session=session):
                yield chunk
            
            # Update statistics after streaming completes
            if self.enable_statistics:
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                if was_cached:
                    self.stats["cache_hits"] += 1
                
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            
            # Update failure stats
            if self.enable_statistics:
                self.stats["total_queries"] += 1
                self.stats["failed_queries"] += 1
            
            yield f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your question?"
    
    def create_session(self, session_id: str) -> ChatSession:
        """
        Create a chat session for multi-turn conversations.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ChatSession instance
        """
        session = self.session_manager.create_session(session_id)
        return ChatSession(session_id, self, session)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema."""
        return self.schema_extractor.get_schema()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics.
        
        Returns:
            Dictionary with comprehensive statistics including:
            - Query stats (if enabled)
            - Cache stats
            - Connection pool stats
            - Session stats
            - Schema info
        """
        stats = {
            "cache": self.cache_manager.get_stats(),
            "pool": self.connection_manager.get_pool_status(),
            "sessions": self.session_manager.get_stats(),
            "schema_tables": len(self.schema_extractor.get_schema())
        }
        
        if self.enable_statistics:
            stats.update(self.stats)
        
        return stats
    
    def get_session_history(self, session_id: str) -> Optional[list[Dict[str, Any]]]:
        """Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation messages or None if session not found
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        # Get messages from session
        try:
            # Access session storage directly
            messages = session.get_messages() if hasattr(session, 'get_messages') else []
            return messages
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    def list_sessions(self) -> list[str]:
        """List all active session IDs.
        
        Returns:
            List of session IDs
        """
        return self.session_manager.list_sessions()
    
    def get_schema_info(self, include_foreign_keys: bool = True) -> Dict[str, Any]:
        """Get detailed database schema information.
        
        Args:
            include_foreign_keys: Include foreign key relationships
            
        Returns:
            Dictionary with comprehensive schema information including:
            - Tables and their columns
            - Data types
            - Primary keys
            - Foreign key relationships
            - Indexes
        """
        schema = self.schema_extractor.get_schema()
        
        # Build comprehensive schema info
        schema_info = {
            "tables": {},
            "total_tables": len(schema),
            "relationships": [] if include_foreign_keys else None
        }
        
        for table_name, table_data in schema.items():
            table_info = {
                "name": table_name,
                "columns": table_data.get("columns", []),
                "primary_keys": [
                    col["name"] for col in table_data.get("columns", [])
                    if col.get("primary_key", False)
                ],
                "foreign_keys": table_data.get("foreign_keys", []) if include_foreign_keys else None,
                "indexes": table_data.get("indexes", []),
            }
            
            schema_info["tables"][table_name] = table_info
            
            # Build relationships
            if include_foreign_keys:
                for fk in table_data.get("foreign_keys", []):
                    schema_info["relationships"].append({
                        "from_table": table_name,
                        "from_columns": fk.get("constrained_columns", []),
                        "to_table": fk.get("referred_table"),
                        "to_columns": fk.get("referred_columns", []),
                    })
        
        return schema_info
    
    def clear_session(self, session_id: str) -> None:
        """Clear a session's conversation history.
        
        Args:
            session_id: Session identifier
        """
        import asyncio
        asyncio.run(self.session_manager.clear_session(session_id))
        logger.info(f"Session cleared: {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session.
        
        Args:
            session_id: Session identifier
        """
        self.session_manager.delete_session(session_id)
        logger.info(f"Session deleted: {session_id}")
    
    @classmethod
    def from_env(cls, **overrides) -> "DatabaseQueryAgent":
        """Create agent from environment variables with optional overrides.
        
        This is the recommended way to create an agent when using .env configuration.
        
        Args:
            **overrides: Any parameters to override from .env
            
        Returns:
            DatabaseQueryAgent instance
            
        Example:
            >>> # Load everything from .env
            >>> agent = DatabaseQueryAgent.from_env()
            >>> 
            >>> # Override specific values
            >>> agent = DatabaseQueryAgent.from_env(
            ...     read_only=False,
            ...     fast_model="gpt-4.1"
            ... )
        """
        return cls(**overrides)
    
    def close(self) -> None:
        """Close all connections and cleanup."""
        logger.info("Closing DatabaseQueryAgent")
        self.connection_manager.close()
