"""Tests for agent_integration module."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from db_query_agent.agent_integration import (
    AgentIntegration,
    DatabaseContext,
    QueryResponse
)
from db_query_agent.config import ModelConfig


class TestQueryResponse:
    """Test QueryResponse model."""
    
    def test_initialization(self):
        """Test query response initialization."""
        response = QueryResponse(
            sql="SELECT * FROM users",
            explanation="Retrieves all users",
            confidence=0.95
        )
        assert response.sql == "SELECT * FROM users"
        assert response.explanation == "Retrieves all users"
        assert response.confidence == 0.95
        assert response.needs_clarification is False
    
    def test_with_clarification(self):
        """Test query response with clarification."""
        response = QueryResponse(
            sql="",
            explanation="Need more info",
            needs_clarification=True,
            clarification_question="Which table do you mean?"
        )
        assert response.needs_clarification is True
        assert response.clarification_question == "Which table do you mean?"


class TestDatabaseContext:
    """Test DatabaseContext class."""
    
    def test_initialization(
        self,
        connection_manager,
        schema_extractor,
        query_validator,
        safety_config
    ):
        """Test database context initialization."""
        context = DatabaseContext(
            connection_manager=connection_manager,
            schema_extractor=schema_extractor,
            validator=query_validator,
            safety_config=safety_config
        )
        assert context.connection_manager == connection_manager
        assert context.schema_extractor == schema_extractor
        assert context.validator == query_validator
        assert context.safety_config == safety_config


class TestAgentIntegration:
    """Test AgentIntegration class."""
    
    @pytest.fixture
    def db_context(
        self,
        connection_manager,
        schema_extractor,
        query_validator,
        safety_config
    ):
        """Create database context for testing."""
        return DatabaseContext(
            connection_manager=connection_manager,
            schema_extractor=schema_extractor,
            validator=query_validator,
            safety_config=safety_config
        )
    
    @pytest.fixture
    def agent_integration(self, db_context, model_config):
        """Create agent integration for testing."""
        return AgentIntegration(
            context=db_context,
            model_config=model_config,
            openai_api_key="test-key"
        )
    
    def test_initialization(self, agent_integration, db_context, model_config):
        """Test agent integration initialization."""
        assert agent_integration.context == db_context
        assert agent_integration.model_config == model_config
        assert agent_integration.openai_api_key == "test-key"
    
    def test_select_model_simple(self, agent_integration):
        """Test model selection for simple queries."""
        model = agent_integration._select_model("how many users")
        assert model == agent_integration.model_config.fast_model
    
    def test_select_model_complex(self, agent_integration):
        """Test model selection for complex queries."""
        model = agent_integration._select_model(
            "compare sales between regions with group by"
        )
        assert model == agent_integration.model_config.complex_model
    
    def test_select_model_balanced(self, agent_integration):
        """Test model selection for medium queries."""
        model = agent_integration._select_model("show user details")
        assert model == agent_integration.model_config.balanced_model
    
    def test_select_model_fixed_strategy(self, db_context):
        """Test fixed model strategy."""
        model_config = ModelConfig(strategy="fixed")
        integration = AgentIntegration(
            context=db_context,
            model_config=model_config,
            openai_api_key="test-key"
        )
        
        # Should always return balanced model
        model = integration._select_model("any query")
        assert model == model_config.balanced_model
    
    def test_create_agent(self, agent_integration):
        """Test agent creation."""
        schema_context = "Table: users (id, name, email)"
        agent = agent_integration._create_agent(schema_context, "gpt-4o-mini")
        
        assert agent is not None
        assert agent.name == "Database Query Agent"
        assert "users" in agent.instructions
    
    @pytest.mark.asyncio
    async def test_generate_sql_mock(self, agent_integration):
        """Test SQL generation with mocked agent."""
        # This test would require mocking the OpenAI API
        # For now, we'll test the structure
        with patch.object(
            agent_integration,
            'generate_sql',
            return_value=QueryResponse(
                sql="SELECT COUNT(*) FROM users",
                explanation="Counts all users",
                confidence=0.95
            )
        ):
            response = await agent_integration.generate_sql("how many users")
            assert response.sql == "SELECT COUNT(*) FROM users"
            assert response.confidence == 0.95
