"""Database schema extraction using SQLAlchemy reflection."""

import time
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, inspect, MetaData, Engine
from sqlalchemy.engine import Inspector
from db_query_agent.exceptions import SchemaExtractionError
import logging

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extracts and caches database schema using SQLAlchemy reflection."""
    
    def __init__(self, engine: Engine, cache_ttl: int = 3600):
        """
        Initialize schema extractor.
        
        Args:
            engine: SQLAlchemy engine
            cache_ttl: Cache time-to-live in seconds
        """
        self.engine = engine
        self.cache_ttl = cache_ttl
        self._schema_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        self._inspector: Optional[Inspector] = None
    
    @property
    def inspector(self) -> Inspector:
        """Get or create SQLAlchemy inspector."""
        if self._inspector is None:
            self._inspector = inspect(self.engine)
        return self._inspector
    
    def _is_cache_valid(self) -> bool:
        """Check if cached schema is still valid."""
        if self._schema_cache is None or self._cache_timestamp is None:
            return False
        
        elapsed = time.time() - self._cache_timestamp
        return elapsed < self.cache_ttl
    
    def get_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get complete database schema.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            Dictionary containing schema information
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("Returning cached schema")
            return self._schema_cache
        
        logger.info("Extracting database schema...")
        start_time = time.time()
        
        try:
            schema = self._extract_schema()
            self._schema_cache = schema
            self._cache_timestamp = time.time()
            
            elapsed = time.time() - start_time
            logger.info(f"Schema extracted in {elapsed:.2f}s - {len(schema)} tables found")
            
            return schema
            
        except Exception as e:
            logger.error(f"Schema extraction failed: {e}")
            raise SchemaExtractionError(f"Failed to extract schema: {e}")
    
    def _extract_schema(self) -> Dict[str, Any]:
        """Extract schema from database."""
        schema = {}
        
        # Get all table names
        table_names = self.inspector.get_table_names()
        
        for table_name in table_names:
            schema[table_name] = self._extract_table_info(table_name)
        
        return schema
    
    def _extract_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Extract information for a single table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        table_info = {
            "name": table_name,
            "columns": [],
            "primary_keys": [],
            "foreign_keys": [],
            "indexes": [],
        }
        
        # Get columns
        columns = self.inspector.get_columns(table_name)
        for col in columns:
            table_info["columns"].append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": col.get("default"),
            })
        
        # Get primary key
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        if pk_constraint:
            table_info["primary_keys"] = pk_constraint.get("constrained_columns", [])
        
        # Get foreign keys
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            table_info["foreign_keys"].append({
                "name": fk.get("name"),
                "columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table"),
                "referred_columns": fk.get("referred_columns", []),
            })
        
        # Get indexes
        indexes = self.inspector.get_indexes(table_name)
        for idx in indexes:
            table_info["indexes"].append({
                "name": idx.get("name"),
                "columns": idx.get("column_names", []),
                "unique": idx.get("unique", False),
            })
        
        return table_info
    
    def get_relevant_tables(
        self, 
        query: str, 
        max_tables: int = 5
    ) -> List[str]:
        """
        Find relevant tables for a query using keyword matching.
        
        Args:
            query: User's natural language query
            max_tables: Maximum number of tables to return
            
        Returns:
            List of relevant table names
        """
        schema = self.get_schema()
        query_lower = query.lower()
        keywords = query_lower.split()
        
        # Score tables by keyword matches
        table_scores = {}
        for table_name in schema.keys():
            score = 0
            table_lower = table_name.lower()
            
            # Check if table name appears in query
            if table_lower in query_lower:
                score += 10
            
            # Check if any keyword matches table name
            for keyword in keywords:
                if keyword in table_lower:
                    score += 5
            
            # Check column names
            for col in schema[table_name]["columns"]:
                col_name = col["name"].lower()
                if col_name in query_lower:
                    score += 3
                for keyword in keywords:
                    if keyword in col_name:
                        score += 1
            
            if score > 0:
                table_scores[table_name] = score
        
        # Return top N tables
        sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_tables = [table for table, score in sorted_tables[:max_tables]]
        
        # If no matches, return all tables (up to max)
        if not relevant_tables:
            relevant_tables = list(schema.keys())[:max_tables]
        
        logger.debug(f"Found {len(relevant_tables)} relevant tables for query")
        return relevant_tables
    
    def format_for_llm(
        self, 
        tables: Optional[List[str]] = None,
        include_examples: bool = True
    ) -> str:
        """
        Format schema as context for LLM.
        
        Args:
            tables: Specific tables to include (None = all)
            include_examples: Include example queries
            
        Returns:
            Formatted schema string
        """
        schema = self.get_schema()
        
        if tables is None:
            tables = list(schema.keys())
        
        # Build compact schema description
        schema_lines = []
        schema_lines.append("Database Schema:")
        schema_lines.append("")
        
        for table_name in tables:
            if table_name not in schema:
                continue
            
            table_info = schema[table_name]
            
            # Table name and columns
            cols = []
            for col in table_info["columns"]:
                col_str = f"{col['name']} {col['type']}"
                if not col['nullable']:
                    col_str += " NOT NULL"
                if col['name'] in table_info['primary_keys']:
                    col_str += " PRIMARY KEY"
                cols.append(col_str)
            
            schema_lines.append(f"Table: {table_name}")
            schema_lines.append(f"  Columns: {', '.join(cols)}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                fks = []
                for fk in table_info['foreign_keys']:
                    fk_str = f"{','.join(fk['columns'])} -> {fk['referred_table']}({','.join(fk['referred_columns'])})"
                    fks.append(fk_str)
                schema_lines.append(f"  Foreign Keys: {'; '.join(fks)}")
            
            schema_lines.append("")
        
        return "\n".join(schema_lines)
    
    def get_dialect(self) -> str:
        """Get database dialect name."""
        return self.engine.dialect.name
