"""
Pytest configuration and fixtures for Aivta project.
"""

import pytest
import asyncio
from typing import AsyncGenerator
import os
import sys

# Add the services directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))

from core.config import Settings
from core.database import Database
from core.llm_service import LLMService
from core.game_interface import GameInterface
from core.agent import AIAgent


@pytest.fixture
def settings():
    """Test settings with test database."""
    return Settings(
        database_url="postgresql://test_user:test_pass@localhost:5432/test_aivta",
        openai_api_key="test_key",
        ollama_host="http://localhost:11434",
        text_game_host="localhost",
        text_game_port=8080,
        log_level="DEBUG"
    )


@pytest.fixture
async def database(settings):
    """Test database instance."""
    db = Database(settings.database_url)
    await db.initialize()
    yield db
    await db.shutdown()


@pytest.fixture
async def llm_service(settings):
    """Test LLM service instance."""
    service = LLMService(settings)
    await service.initialize()
    yield service
    await service.shutdown()


@pytest.fixture
async def game_interface(settings):
    """Test game interface instance."""
    interface = GameInterface(settings)
    await interface.initialize()
    yield interface
    await interface.shutdown()


@pytest.fixture
async def ai_agent(database, llm_service, game_interface):
    """Test AI agent instance."""
    agent = AIAgent(database, llm_service, game_interface)
    await agent.initialize()
    yield agent
    await agent.shutdown()


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