"""
Simplified pytest configuration and fixtures for Aivta project.
"""

import pytest
import asyncio
import os
import sys

# Add the services directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))

# Only import what we can actually use
try:
    from core.config import Settings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: Config module not available")


@pytest.fixture
def settings():
    """Test settings."""
    if not CONFIG_AVAILABLE:
        pytest.skip("Config module not available")
    
    return Settings(
        database_url="postgresql://test_user:test_pass@localhost:5432/test_aivta",
        openai_api_key="test_key",
        ollama_host="http://localhost:11434",
        text_game_host="localhost",
        text_game_port=8080,
        log_level="DEBUG"
    )


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_game_session():
    """Sample game session data for testing."""
    return {
        "session_id": "test_session_123",
        "game_type": "adventure",
        "status": "active"
    }


@pytest.fixture
def sample_game_state():
    """Sample game state data for testing."""
    return {
        "state_hash": "test_hash_123",
        "game_description": "You are at the entrance of a cave.",
        "available_actions": ["go north", "go east", "look around"],
        "inventory": ["torch"],
        "location": "entrance",
        "score": 0
    }