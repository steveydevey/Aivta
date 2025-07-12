"""
Aivta Text Game Service
A containerized text-based adventure game service.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from game_engine import AdventureGame
from config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
game_engine = AdventureGame()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Text Game Service")
    
    # Initialize game engine
    await game_engine.initialize()
    
    logger.info("Text Game Service initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Text Game Service")
    await game_engine.shutdown()


# FastAPI app
app = FastAPI(
    title="Aivta Text Game",
    description="Text-based adventure game service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class GameState(BaseModel):
    """Game state model."""
    session_id: str
    current_location: str
    description: str
    inventory: List[str] = Field(default_factory=list)
    score: int = 0
    moves: int = 0
    game_over: bool = False
    victory: bool = False


class GameCommand(BaseModel):
    """Game command model."""
    session_id: str
    command: str


class GameResponse(BaseModel):
    """Game response model."""
    session_id: str
    response: str
    game_state: GameState
    valid_commands: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class GameSession(BaseModel):
    """Game session model."""
    session_id: str
    game_type: str
    status: str
    created_at: str
    last_action: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "text-game",
        "version": "1.0.0",
        "active_sessions": await game_engine.get_active_sessions_count()
    }


# Game session endpoints
@app.post("/sessions", response_model=GameSession)
async def create_session(game_type: str = "adventure"):
    """Create a new game session."""
    try:
        session = await game_engine.create_session(game_type)
        return GameSession(
            session_id=session.session_id,
            game_type=session.game_type,
            status=session.status,
            created_at=session.created_at
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=GameState)
async def get_session_state(session_id: str):
    """Get current game state for a session."""
    try:
        state = await game_engine.get_game_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return GameState(**state)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/commands", response_model=GameResponse)
async def execute_command(session_id: str, command: GameCommand):
    """Execute a command in the game."""
    try:
        response = await game_engine.execute_command(
            session_id=session_id,
            command=command.command
        )
        
        return GameResponse(
            session_id=session_id,
            response=response.response,
            game_state=GameState(**response.game_state),
            valid_commands=response.valid_commands,
            error=response.error
        )
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/valid-commands")
async def get_valid_commands(session_id: str):
    """Get valid commands for current game state."""
    try:
        commands = await game_engine.get_valid_commands(session_id)
        return {"session_id": session_id, "valid_commands": commands}
    except Exception as e:
        logger.error(f"Error getting valid commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session."""
    try:
        await game_engine.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Game management endpoints
@app.get("/game-info")
async def get_game_info():
    """Get information about the game."""
    try:
        info = await game_engine.get_game_info()
        return info
    except Exception as e:
        logger.error(f"Error getting game info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    try:
        sessions = await game_engine.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/save")
async def save_game(session_id: str):
    """Save game state to file."""
    try:
        filename = await game_engine.save_game(session_id)
        return {"message": "Game saved successfully", "filename": filename}
    except Exception as e:
        logger.error(f"Error saving game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/load")
async def load_game(session_id: str, filename: str):
    """Load game state from file."""
    try:
        await game_engine.load_game(session_id, filename)
        return {"message": "Game loaded successfully"}
    except Exception as e:
        logger.error(f"Error loading game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)