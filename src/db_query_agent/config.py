"""Configuration management for db-query-agent."""

from typing import Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")
    
    # SSL Configuration
    ssl_enabled: Optional[bool] = Field(default=None, description="Enable SSL (auto-detected from URL if None)")
    ssl_cert: Optional[str] = Field(default=None, description="Path to SSL certificate file")
    ssl_key: Optional[str] = Field(default=None, description="Path to SSL key file")
    ssl_ca: Optional[str] = Field(default=None, description="Path to SSL CA certificate")
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates")
    
    # Additional connection arguments
    connect_args: Optional[dict] = Field(default=None, description="Additional connection arguments")


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    enabled: bool = Field(default=True, description="Enable caching")
    backend: str = Field(default="memory", description="Cache backend: memory, sqlite, redis")
    schema_ttl: int = Field(default=3600, description="Schema cache TTL in seconds")
    query_ttl: int = Field(default=300, description="Query result cache TTL in seconds")
    llm_ttl: int = Field(default=3600, description="LLM response cache TTL in seconds")
    redis_url: Optional[str] = Field(default=None, description="Redis URL if using redis backend")


class ModelConfig(BaseModel):
    """LLM model configuration."""
    
    strategy: str = Field(default="adaptive", description="Model selection strategy: fixed, adaptive")
    fast_model: str = Field(default="gpt-4o-mini", description="Fast model for simple queries")
    balanced_model: str = Field(default="gpt-4.1-mini", description="Balanced model")
    complex_model: str = Field(default="gpt-4.1", description="Complex model for hard queries")
    temperature: float = Field(default=0.0, description="Model temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens for response")


class SafetyConfig(BaseModel):
    """Safety and validation configuration."""
    
    read_only: bool = Field(default=True, description="Allow only SELECT queries")
    allowed_tables: Optional[List[str]] = Field(default=None, description="Allowed tables (None = all)")
    blocked_tables: Optional[List[str]] = Field(default=None, description="Blocked tables")
    max_query_timeout: int = Field(default=30, description="Maximum query execution time in seconds")
    max_result_rows: int = Field(default=10000, description="Maximum result rows")
    enable_guardrails: bool = Field(default=True, description="Enable input/output guardrails")


class AgentConfig(BaseModel):
    """Complete agent configuration."""
    
    openai_api_key: str = Field(..., description="OpenAI API key")
    database: DatabaseConfig
    cache: CacheConfig = Field(default_factory=CacheConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    
    enable_streaming: bool = Field(default=True, description="Enable streaming responses")
    lazy_schema_loading: bool = Field(default=True, description="Load only relevant tables")
    max_tables_in_context: int = Field(default=5, description="Max tables to include in context")
    use_embeddings: bool = Field(default=False, description="Use embeddings for table selection")
    warmup_on_init: bool = Field(default=False, description="Warm up cache on initialization")
    
    @classmethod
    def from_env(
        cls,
        database_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        **overrides
    ) -> "AgentConfig":
        """Create configuration from environment variables with optional overrides.
        
        Args:
            database_url: Database URL (overrides env)
            openai_api_key: OpenAI API key (overrides env)
            **overrides: Any other config parameters to override
        
        Returns:
            AgentConfig instance
        """
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
        
        # Build config from env with overrides
        config_dict = {
            "openai_api_key": api_key,
            "database": DatabaseConfig(
                url=db_url,
                pool_size=int(get_env("DB_POOL_SIZE", "10")),
                max_overflow=int(get_env("DB_MAX_OVERFLOW", "20")),
            ),
            "cache": CacheConfig(
                enabled=get_env("CACHE_ENABLED", "true").lower() == "true",
                backend=get_env("CACHE_BACKEND", "memory"),
                redis_url=get_env("REDIS_URL"),
                schema_ttl=int(get_env("CACHE_SCHEMA_TTL", "3600")),
                query_ttl=int(get_env("CACHE_QUERY_TTL", "300")),
                llm_ttl=int(get_env("CACHE_LLM_TTL", "3600")),
            ),
            "model": ModelConfig(
                strategy=get_env("MODEL_STRATEGY", "adaptive"),
                fast_model=get_env("FAST_MODEL", "gpt-4o-mini"),
                balanced_model=get_env("BALANCED_MODEL", "gpt-4.1-mini"),
                complex_model=get_env("COMPLEX_MODEL", "gpt-4.1"),
                temperature=float(get_env("MODEL_TEMPERATURE", "0.0")),
                max_tokens=int(get_env("MODEL_MAX_TOKENS", "1000")),
            ),
            "safety": SafetyConfig(
                read_only=get_env("READ_ONLY", "true").lower() == "true",
                max_query_timeout=int(get_env("QUERY_TIMEOUT", "30")),
                max_result_rows=int(get_env("MAX_RESULT_ROWS", "10000")),
            ),
            "enable_streaming": get_env("ENABLE_STREAMING", "true").lower() == "true",
            "lazy_schema_loading": get_env("LAZY_SCHEMA_LOADING", "true").lower() == "true",
            "max_tables_in_context": int(get_env("MAX_TABLES_IN_CONTEXT", "5")),
            "warmup_on_init": get_env("WARMUP_ON_INIT", "false").lower() == "true",
        }
        
        # Apply overrides
        config_dict.update(overrides)
        
        return cls(**config_dict)
