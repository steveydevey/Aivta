"""
Tests for database module.
"""

import pytest
import asyncio
from core.database import Database
from core.config import Settings


@pytest.mark.asyncio
async def test_database_initialization(settings):
    """Test database initialization."""
    db = Database(settings.database_url)
    
    # Test initialization
    await db.initialize()
    assert db.is_initialized
    
    # Test shutdown
    await db.shutdown()
    assert not db.is_initialized


@pytest.mark.asyncio
async def test_database_connection_error():
    """Test database connection error handling."""
    invalid_settings = Settings(
        database_url="postgresql://invalid:pass@localhost:9999/invalid_db"
    )
    
    db = Database(invalid_settings.database_url)
    
    with pytest.raises(Exception):
        await db.initialize()


@pytest.mark.asyncio
async def test_database_health_check(settings):
    """Test database health check."""
    db = Database(settings.database_url)
    
    try:
        await db.initialize()
        health = await db.health_check()
        assert health["status"] == "healthy"
    finally:
        await db.shutdown()


@pytest.mark.asyncio
async def test_database_session_operations(settings):
    """Test game session database operations."""
    db = Database(settings.database_url)
    
    try:
        await db.initialize()
        
        # Test creating a session
        session_data = {
            "session_id": "test_session_123",
            "game_type": "adventure",
            "status": "active"
        }
        
        session_id = await db.create_game_session(session_data)
        assert session_id is not None
        
        # Test retrieving a session
        session = await db.get_game_session("test_session_123")
        assert session["session_id"] == "test_session_123"
        assert session["game_type"] == "adventure"
        
        # Test updating a session
        await db.update_game_session("test_session_123", {"status": "completed"})
        updated_session = await db.get_game_session("test_session_123")
        assert updated_session["status"] == "completed"
        
    finally:
        await db.shutdown()


@pytest.mark.asyncio
async def test_database_state_operations(settings):
    """Test game state database operations."""
    db = Database(settings.database_url)
    
    try:
        await db.initialize()
        
        # Create a session first
        session_data = {
            "session_id": "test_session_456",
            "game_type": "adventure",
            "status": "active"
        }
        session_id = await db.create_game_session(session_data)
        
        # Test creating a game state
        state_data = {
            "session_id": session_id,
            "state_hash": "test_hash_456",
            "game_description": "You are in a cave.",
            "available_actions": ["go north", "go south"],
            "inventory": ["torch"],
            "location": "cave",
            "score": 10
        }
        
        state_id = await db.create_game_state(state_data)
        assert state_id is not None
        
        # Test retrieving a game state
        state = await db.get_game_state(state_id)
        assert state["game_description"] == "You are in a cave."
        assert state["location"] == "cave"
        
    finally:
        await db.shutdown()