# Test Suite

Comprehensive test suite for db-query-agent package.

## Test Structure

### Phase 1-3 Tests (Existing)
- `test_cache_manager.py` - Cache functionality tests
- `test_config.py` - Configuration tests
- `test_connection_manager.py` - Database connection tests
- `test_query_validator.py` - SQL validation tests
- `test_schema_extractor.py` - Schema extraction tests
- `test_session_manager.py` - Session management tests
- `test_agent_integration.py` - Agent integration tests

### Phase 4 Tests (New)
- `test_dynamic_configuration.py` - Dynamic configuration system tests
  - Direct parameter configuration
  - Environment variable configuration
  - Parameter override priority
  - Default values
  - Configuration classes
  - Statistics configuration
  - Streaming configuration
  - Session configuration

- `test_streaming.py` - Streaming functionality tests
  - Async iterator behavior
  - Session integration
  - Error handling
  - Multi-agent streaming
  - Cache integration
  - Performance tests

- `test_utility_methods.py` - New utility methods tests
  - Session management (list, get history, clear, delete)
  - Schema exploration (get_schema, get_schema_info)
  - Statistics (get_stats with/without query stats)
  - Exported classes verification

- `test_phase4_integration.py` - End-to-end integration tests
  - Complete workflow with streaming
  - Session-based conversations
  - Configuration priority
  - Schema exploration workflow
  - Caching with streaming
  - Statistics tracking
  - Multiple agents independence
  - Error handling
  - Backward compatibility

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_dynamic_configuration.py -v
pytest tests/test_streaming.py -v
pytest tests/test_utility_methods.py -v
pytest tests/test_phase4_integration.py -v
```

### Run Tests by Category
```bash
# Phase 4 tests only
pytest tests/test_dynamic_configuration.py tests/test_streaming.py tests/test_utility_methods.py tests/test_phase4_integration.py -v

# Integration tests only
pytest tests/test_phase4_integration.py tests/test_agent_integration.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=db_agent_sql --cov-report=html
```

### Run Async Tests Only
```bash
pytest tests/ -v -k "asyncio"
```

## Test Coverage

### Phase 4 Features Covered
✅ Dynamic configuration (parameter, .env, defaults)
✅ Streaming functionality (token-by-token)
✅ Session utility methods (list, history, clear, delete)
✅ Schema exploration (basic and detailed)
✅ Statistics tracking (optional)
✅ Configuration priority (parameter > env > default)
✅ Backward compatibility
✅ Error handling
✅ Multi-agent streaming
✅ Cache integration with streaming

### Test Statistics
- **Total Test Files**: 11
- **Phase 4 Test Files**: 4
- **Test Classes**: 30+
- **Test Methods**: 80+

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `mock_db_context` - Mock database context
- `mock_model_config` - Mock model configuration
- `agent` - Basic agent instance
- Database setup/teardown

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No external dependencies required
- Uses SQLite in-memory databases
- Mocked OpenAI API calls
- Fast execution (< 30 seconds)

## Writing New Tests

### Test Naming Convention
- Test files: `test_<feature>.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<specific_behavior>`

### Example Test
```python
import pytest
from db_agent_sql import DatabaseQueryAgent

class TestNewFeature:
    """Test new feature."""
    
    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DatabaseQueryAgent(
            database_url="sqlite:///:memory:",
            openai_api_key="sk-test-key"
        )
    
    def test_feature_behavior(self, agent):
        """Test specific behavior."""
        result = agent.some_method()
        assert result is not None
        agent.close()
```

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "Event loop is closed"
**Solution**: Use `@pytest.mark.asyncio` for async tests

**Issue**: Import errors
**Solution**: Install package in development mode: `pip install -e .`

**Issue**: Mock not working
**Solution**: Ensure correct import path in `@patch` decorator

## Future Tests

Planned test additions:
- Performance benchmarks
- Load testing
- Security testing
- API integration tests
- UI component tests (Streamlit)
