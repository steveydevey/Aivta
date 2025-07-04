"""
Aivta AI Agent Service
Main FastAPI application for coordinating between LLM and text-based games.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.agent import AIAgent
from core.database import Database
from core.llm_service import LLMService
from core.game_interface import GameInterface
from core.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
database = Database(settings.database_url)
llm_service = LLMService(settings)
game_interface = GameInterface(settings)
ai_agent = AIAgent(database, llm_service, game_interface)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Aivta AI Agent Service")
    
    # Initialize database
    await database.initialize()
    
    # Initialize services
    await llm_service.initialize()
    await game_interface.initialize()
    await ai_agent.initialize()
    
    logger.info("AI Agent Service initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down AI Agent Service")
    await ai_agent.shutdown()
    await game_interface.shutdown()
    await llm_service.shutdown()
    await database.shutdown()


# FastAPI app
app = FastAPI(
    title="Aivta AI Agent",
    description="AI Agent for coordinating LLM and text-based game interactions",
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
class GameSession(BaseModel):
    """Game session model."""
    session_id: str
    game_type: str
    status: str = "active"
    current_state: Optional[str] = None
    path_history: list = Field(default_factory=list)


class GameAction(BaseModel):
    """Game action model."""
    session_id: str
    action: str
    context: Optional[str] = None


class GameResponse(BaseModel):
    """Game response model."""
    session_id: str
    response: str
    game_state: str
    action_successful: bool
    game_completed: bool = False


class AgentStats(BaseModel):
    """Agent statistics model."""
    total_sessions: int
    active_sessions: int
    completed_games: int
    success_rate: float
    average_actions_per_game: float


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-agent",
        "version": "1.0.0",
        "database": await database.health_check(),
        "llm_service": await llm_service.health_check(),
        "game_interface": await game_interface.health_check()
    }


# Game session endpoints
@app.post("/sessions", response_model=GameSession)
async def create_game_session(game_type: str = "adventure"):
    """Create a new game session."""
    try:
        session = await ai_agent.create_session(game_type)
        return GameSession(
            session_id=session.session_id,
            game_type=session.game_type,
            status=session.status,
            current_state=session.current_state
        )
    except Exception as e:
        logger.error(f"Error creating game session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=GameSession)
async def get_game_session(session_id: str):
    """Get game session details."""
    try:
        session = await ai_agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return GameSession(
            session_id=session.session_id,
            game_type=session.game_type,
            status=session.status,
            current_state=session.current_state,
            path_history=session.path_history
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/actions", response_model=GameResponse)
async def execute_action(session_id: str, action: GameAction):
    """Execute an action in the game."""
    try:
        response = await ai_agent.execute_action(
            session_id=session_id,
            action=action.action,
            context=action.context
        )
        
        return GameResponse(
            session_id=session_id,
            response=response.response,
            game_state=response.game_state,
            action_successful=response.action_successful,
            game_completed=response.game_completed
        )
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/play")
async def start_autonomous_play(session_id: str, background_tasks: BackgroundTasks):
    """Start autonomous gameplay for a session."""
    try:
        background_tasks.add_task(ai_agent.play_game_autonomously, session_id)
        return {"message": "Autonomous gameplay started", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error starting autonomous play: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/path")
async def get_game_path(session_id: str):
    """Get the path taken through the game."""
    try:
        path = await ai_agent.get_game_path(session_id)
        return {"session_id": session_id, "path": path}
    except Exception as e:
        logger.error(f"Error getting game path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session."""
    try:
        await ai_agent.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent management endpoints
@app.get("/stats", response_model=AgentStats)
async def get_agent_stats():
    """Get AI agent statistics."""
    try:
        stats = await ai_agent.get_stats()
        return AgentStats(**stats)
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_agent():
    """Reset the AI agent (clear all sessions)."""
    try:
        await ai_agent.reset()
        return {"message": "Agent reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoints
@app.get("/debug/llm")
async def test_llm_connection():
    """Test LLM service connection."""
    try:
        result = await llm_service.test_connection()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error testing LLM connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/game")
async def test_game_connection():
    """Test game service connection."""
    try:
        result = await game_interface.test_connection()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error testing game connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)