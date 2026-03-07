"""Simple Multi-Agent System - Fast, conversational-first architecture."""

import logging
from typing import Dict, Any, Optional, AsyncIterator
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent
from db_query_agent.agents.simple_sql_agent import SimpleSQLAgent
from db_query_agent.agents.simple_conversational_agent import SimpleConversationalAgent
from db_query_agent.agent_integration import DatabaseContext
from db_query_agent.config import ModelConfig

logger = logging.getLogger(__name__)


class SimpleMultiAgentSystem:
    """
    Simple multi-agent system with conversational-first architecture.
    
    Architecture:
    - Conversational Agent: Main interface (handles ALL user interactions)
    - SQL Agent: Backend worker (generates and executes SQL as a tool)
    
    Speed: 1 LLM call per query (optimized for speed)
    """
    
    def __init__(
        self,
        database_context: DatabaseContext,
        model_config: ModelConfig,
        openai_api_key: str,
        cache_manager: Optional[Any] = None,
        cache_enabled: bool = True
    ):
        """Initialize simple multi-agent system."""
        logger.info("Creating simple multi-agent system...")
        
        self.db_context = database_context
        self.dialect = database_context.connection_manager.engine.dialect.name
        self.cache_manager = cache_manager
        self.cache_enabled = cache_enabled
        self.model_config = model_config
        self.openai_api_key = openai_api_key
        
        # Get SQL dialect
        self.dialect = database_context.schema_extractor.get_dialect()
        
        logger.info("Creating simple multi-agent system...")
        
        # Create SQL Agent (backend worker)
        logger.info("Creating SQL Agent...")
        self.sql_agent = SimpleSQLAgent.create(
            model=model_config.fast_model,  # Use fast model for SQL
            dialect=self.dialect
        )
        
        # Create Conversational Agent (main interface)
        logger.info("Creating Conversational Agent...")
        self.conversational_agent = SimpleConversationalAgent.create(
            sql_agent=self.sql_agent,
            model=model_config.balanced_model  # Use balanced model for conversation
        )
        
        logger.info("Simple multi-agent system initialized successfully")
        logger.info(f"Architecture: Conversational Agent → SQL Agent (as tool)")
        logger.info(f"Speed: 1 LLM call per query (optimized for speed)")
    
    async def query(
        self,
        question: str,
        session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Process a query through the conversational agent.
        
        Args:
            question: User's natural language question
            session: Optional session for conversation history
            
        Returns:
            Response dictionary with results
        """
        logger.info(f"Processing query: {question}")
        
        try:
            # Check cache first (if enabled)
            if self.cache_enabled and self.cache_manager:
                schema_hash = str(hash(str(self.db_context.schema_extractor.get_schema())))
                cached = self.cache_manager.get_llm_response(question, schema_hash)
                if cached:
                    logger.info("Returning cached response")
                    return cached
            
            # Run conversational agent - it will call SQL agent as tool if needed
            result = await Runner.run(
                self.conversational_agent,
                input=question,
                context=self.db_context,
                session=session
            )
            
            # Extract response (pure conversational - no SQL exposed)
            response = {
                "question": question,
                "final_output": str(result.final_output),
                "natural_response": str(result.final_output),
                "agent_used": "Conversational Agent",
            }
            
            # Cache the response (if enabled)
            if self.cache_enabled and self.cache_manager:
                self.cache_manager.set_llm_response(question, schema_hash, response)
            
            logger.info(f"Query completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "question": question,
                "error": str(e),
                "final_output": f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your question?",
                "natural_response": f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your question?"
            }
    
    async def query_stream(
        self,
        question: str,
        session: Optional[Any] = None
    ) -> AsyncIterator[str]:
        """
        Process a query with streaming response (token-by-token).
        
        Args:
            question: User's natural language question
            session: Optional session for conversation history
            
        Yields:
            Text chunks as they are generated
        """
        logger.info(f"Processing streaming query: {question}")
        
        try:
            # Check cache first (if enabled)
            if self.cache_enabled and self.cache_manager:
                schema_hash = str(hash(str(self.db_context.schema_extractor.get_schema())))
                cached = self.cache_manager.get_llm_response(question, schema_hash)
                if cached:
                    logger.info("Returning cached response (streaming)")
                    # Yield cached response all at once
                    yield cached.get("natural_response", str(cached.get("final_output", "")))
                    return
            
            # Run conversational agent with streaming
            result = Runner.run_streamed(
                self.conversational_agent,
                input=question,
                context=self.db_context,
                session=session
            )
            
            # Stream text deltas as they arrive
            full_response = ""
            async for event in result.stream_events():
                # Only stream raw text deltas (token-by-token)
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    full_response += delta
                    yield delta
            
            # Cache the complete response (if enabled)
            if self.cache_enabled and self.cache_manager and full_response:
                response = {
                    "question": question,
                    "final_output": full_response,
                    "natural_response": full_response,
                    "agent_used": "Conversational Agent",
                }
                self.cache_manager.set_llm_response(question, schema_hash, response)
            
            logger.info(f"Streaming query completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your question?"
            yield error_msg
    
    def get_agents(self) -> Dict[str, Agent[DatabaseContext]]:
        """
        Get all agents in the system.
        
        Returns:
            Dictionary of agent name to agent instance
        """
        return {
            "conversational": self.conversational_agent,
            "sql": self.sql_agent,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the multi-agent system.
        
        Returns:
            Dictionary with system statistics
        """
        return {
            "architecture": "Simple Multi-Agent (Conversational-First)",
            "total_agents": 2,
            "agents": {
                "conversational": "Main interface - handles ALL user interactions",
                "sql": "Backend tool - generates and executes SQL (user never sees it)",
            },
            "llm_calls_per_query": 1,
            "speed": "Optimized (1 LLM call)",
            "dialect": self.dialect,
            "model_config": {
                "conversational_model": self.model_config.balanced_model,
                "sql_model": self.model_config.fast_model,
            }
        }
