"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import os
from typing import Generator
from unittest.mock import Mock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    db = Mock()
    db.initialize = AsyncMock()
    db.shutdown = AsyncMock()
    db.health_check = AsyncMock(return_value={"status": "healthy"})
    return db


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    llm = Mock()
    llm.initialize = AsyncMock()
    llm.shutdown = AsyncMock()
    llm.health_check = AsyncMock(return_value={"status": "healthy"})
    llm.test_connection = AsyncMock(return_value={"status": "connected"})
    return llm


@pytest.fixture
def mock_game_interface():
    """Mock game interface for testing."""
    game = Mock()
    game.initialize = AsyncMock()
    game.shutdown = AsyncMock()
    game.health_check = AsyncMock(return_value={"status": "healthy"})
    game.test_connection = AsyncMock(return_value={"status": "connected"})
    return game


@pytest.fixture
def test_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-123",
        "game_type": "adventure",
        "status": "active",
        "current_state": "Forest Clearing",
        "path_history": []
    }


@pytest.fixture
def test_game_state():
    """Sample game state for testing."""
    return {
        "session_id": "test-session-123",
        "current_location": "Forest Clearing",
        "description": "You are in a small clearing in a dark forest.",
        "inventory": [],
        "score": 0,
        "moves": 0,
        "game_over": False,
        "victory": False
    }


@pytest.fixture
def test_game_response():
    """Sample game response for testing."""
    return {
        "session_id": "test-session-123",
        "response": "You look around the forest clearing.",
        "game_state": "Forest Clearing",
        "action_successful": True,
        "game_completed": False
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set test environment variables
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["TESTING"] = "true"
    
    yield
    
    # Clean up
    test_vars = ["DATABASE_URL", "OPENAI_API_KEY", "LOG_LEVEL", "TESTING"]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture
def cleanup_test_files():
    """Clean up test files after tests."""
    created_files = []
    
    def track_file(filename):
        created_files.append(filename)
    
    yield track_file
    
    # Clean up created files
    for filename in created_files:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Warning: Could not clean up file {filename}: {e}")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.name.lower() or "Integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        if "unit" in item.name.lower() or "Unit" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "slow" in item.name.lower() or "Slow" in item.name:
            item.add_marker(pytest.mark.slow)