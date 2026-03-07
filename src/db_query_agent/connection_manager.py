"""Database connection management with pooling."""

from typing import Any, List, Tuple
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from db_query_agent.exceptions import ConnectionError, QueryExecutionError
from db_query_agent.config import DatabaseConfig
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages database connections with pooling."""
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize connection manager.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self._engine: Engine = None
        self._create_engine()
    
    def _create_engine(self) -> None:
        """Create SQLAlchemy engine with connection pooling."""
        try:
            # Build connect_args for SSL and other options
            connect_args = self._build_connect_args()
            
            self._engine = create_engine(
                self.config.url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Verify connections before using
                connect_args=connect_args,
                echo=False
            )
            logger.info(f"Database engine created: {self._engine.dialect.name}")
            if connect_args:
                logger.info(f"Connection args: {list(connect_args.keys())}")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise ConnectionError(f"Failed to create database engine: {e}")
    
    def _build_connect_args(self) -> dict:
        """Build connection arguments including SSL configuration."""
        connect_args = {}
        
        # Start with user-provided connect_args
        if self.config.connect_args:
            connect_args.update(self.config.connect_args)
        
        # Detect database type from URL
        url_lower = self.config.url.lower()
        
        # PostgreSQL SSL configuration
        if 'postgresql' in url_lower or 'postgres' in url_lower:
            ssl_args = self._build_postgresql_ssl_args()
            if ssl_args:
                connect_args.update(ssl_args)
        
        # MySQL SSL configuration
        elif 'mysql' in url_lower:
            ssl_args = self._build_mysql_ssl_args()
            if ssl_args:
                connect_args.update(ssl_args)
        
        # SQL Server SSL configuration
        elif 'mssql' in url_lower or 'sqlserver' in url_lower:
            ssl_args = self._build_sqlserver_ssl_args()
            if ssl_args:
                connect_args.update(ssl_args)
        
        return connect_args
    
    def _build_postgresql_ssl_args(self) -> dict:
        """Build PostgreSQL-specific SSL arguments."""
        ssl_args = {}
        
        # Check if SSL is explicitly enabled or if cert files are provided
        if self.config.ssl_enabled or self.config.ssl_cert:
            import ssl as ssl_module
            
            # Build SSL context
            if self.config.ssl_verify:
                ssl_context = ssl_module.create_default_context()
            else:
                ssl_context = ssl_module.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl_module.CERT_NONE
            
            # Add certificate files if provided
            if self.config.ssl_cert and self.config.ssl_key:
                ssl_context.load_cert_chain(
                    certfile=self.config.ssl_cert,
                    keyfile=self.config.ssl_key
                )
            
            if self.config.ssl_ca:
                ssl_context.load_verify_locations(cafile=self.config.ssl_ca)
            
            ssl_args['ssl'] = ssl_context
            logger.info("PostgreSQL SSL enabled")
        
        elif 'sslmode' not in self.config.url:
            # If no SSL config and no sslmode in URL, check if URL has SSL params
            if '?' not in self.config.url or 'ssl' not in self.config.url.lower():
                logger.info("PostgreSQL SSL not configured (will use URL parameters if present)")
        
        return ssl_args
    
    def _build_mysql_ssl_args(self) -> dict:
        """Build MySQL-specific SSL arguments."""
        ssl_args = {}
        
        if self.config.ssl_enabled or self.config.ssl_cert:
            ssl_config = {}
            
            if self.config.ssl_ca:
                ssl_config['ca'] = self.config.ssl_ca
            
            if self.config.ssl_cert:
                ssl_config['cert'] = self.config.ssl_cert
            
            if self.config.ssl_key:
                ssl_config['key'] = self.config.ssl_key
            
            if not self.config.ssl_verify:
                ssl_config['check_hostname'] = False
                ssl_config['verify_mode'] = False
            
            if ssl_config:
                ssl_args['ssl'] = ssl_config
                logger.info("MySQL SSL enabled")
        
        return ssl_args
    
    def _build_sqlserver_ssl_args(self) -> dict:
        """Build SQL Server-specific SSL arguments."""
        ssl_args = {}
        
        # SQL Server uses TrustServerCertificate and Encrypt in connection string
        # These are typically in the URL, but we can add them to connect_args
        if self.config.ssl_enabled is False:
            ssl_args['TrustServerCertificate'] = 'yes'
            ssl_args['Encrypt'] = 'no'
            logger.info("SQL Server SSL disabled")
        elif self.config.ssl_enabled:
            ssl_args['Encrypt'] = 'yes'
            if not self.config.ssl_verify:
                ssl_args['TrustServerCertificate'] = 'yes'
            logger.info("SQL Server SSL enabled")
        
        return ssl_args
    
    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine."""
        if self._engine is None:
            self._create_engine()
        return self._engine
    
    def execute_query(
        self,
        sql: str,
        timeout: int = 30
    ) -> List[Tuple[Any, ...]]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query to execute
            timeout: Query timeout in seconds
            
        Returns:
            List of result tuples
        """
        try:
            with self.engine.connect() as conn:
                # Set query timeout
                result = conn.execute(
                    text(sql),
                    execution_options={"timeout": timeout}
                )
                
                # Fetch all results
                rows = result.fetchall()
                logger.debug(f"Query executed successfully: {len(rows)} rows returned")
                return rows
                
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Query execution failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise QueryExecutionError(f"Unexpected error: {e}")
    
    async def execute_query_async(
        self,
        sql: str,
        timeout: int = 30
    ) -> List[Tuple[Any, ...]]:
        """
        Execute SQL query asynchronously.
        
        Args:
            sql: SQL query to execute
            timeout: Query timeout in seconds
            
        Returns:
            List of result tuples
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.execute_query,
            sql,
            timeout
        )
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close all database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
    
    def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if not self._engine:
            return {}
        
        pool = self._engine.pool
        
        # Handle both QueuePool (methods) and other pool types (attributes)
        try:
            size = pool.size() if callable(pool.size) else pool.size
            checked_in = pool.checkedin() if callable(pool.checkedin) else getattr(pool, 'checkedin', 0)
            checked_out = pool.checkedout() if callable(pool.checkedout) else getattr(pool, 'checkedout', 0)
            overflow = pool.overflow() if callable(pool.overflow) else getattr(pool, 'overflow', 0)
            
            return {
                "size": size,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
                "total": size + overflow
            }
        except (AttributeError, TypeError):
            # Fallback for pools without these methods/attributes
            return {
                "size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
                "total": 0
            }
