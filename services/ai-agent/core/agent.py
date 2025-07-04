"""Main AI Agent for coordinating LLM and game interactions."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid

from .database import Database
from .llm_service import LLMService
from .game_interface import GameInterface

logger = logging.getLogger(__name__)


@dataclass
class GameSession:
    """Represents a game session."""
    session_id: str
    game_type: str
    game_id: str
    status: str
    current_state: str
    path_history: List[Dict[str, Any]]


@dataclass
class ActionResponse:
    """Represents a game action response."""
    response: str
    game_state: str
    action_successful: bool
    game_completed: bool


class AIAgent:
    """Main AI Agent for coordinating LLM and game interactions."""
    
    def __init__(self, database: Database, llm_service: LLMService, game_interface: GameInterface):
        self.database = database
        self.llm_service = llm_service
        self.game_interface = game_interface
        self.active_sessions: Dict[str, GameSession] = {}
        
    async def initialize(self):
        """Initialize the AI agent."""
        try:
            # Load any existing active sessions from database
            await self._load_active_sessions()
            logger.info("AI Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI agent: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the AI agent."""
        # Save any active sessions
        for session in self.active_sessions.values():
            await self._save_session(session)
        
        logger.info("AI Agent shutdown complete")
    
    async def _load_active_sessions(self):
        """Load active sessions from database."""
        # This would typically load from database
        # For now, we'll start with an empty session dict
        self.active_sessions = {}
    
    async def _save_session(self, session: GameSession):
        """Save session to database."""
        await self.database.update_session(
            session.session_id,
            status=session.status,
            current_state=session.current_state,
            path_history=session.path_history
        )
    
    async def create_session(self, game_type: str = "adventure") -> GameSession:
        """Create a new game session."""
        try:
            # Create session in database
            session_id = await self.database.create_session(game_type)
            
            # Start game
            game_result = await self.game_interface.start_game(game_type)
            
            # Create session object
            session = GameSession(
                session_id=session_id,
                game_type=game_type,
                game_id=game_result.get("game_id", f"game_{session_id}"),
                status="active",
                current_state=game_result.get("initial_state", "Game started"),
                path_history=[]
            )
            
            # Store in memory
            self.active_sessions[session_id] = session
            
            # Save to database
            await self._save_session(session)
            
            logger.info(f"Created new game session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating game session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[GameSession]:
        """Get game session details."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from database
        session_data = await self.database.get_session(session_id)
        if session_data:
            session = GameSession(
                session_id=session_data["session_id"],
                game_type=session_data["game_type"],
                game_id=session_data.get("game_id", f"game_{session_id}"),
                status=session_data["status"],
                current_state=session_data.get("current_state", ""),
                path_history=session_data.get("path_history", [])
            )
            self.active_sessions[session_id] = session
            return session
        
        return None
    
    async def execute_action(self, session_id: str, action: str, 
                           context: Optional[str] = None) -> ActionResponse:
        """Execute an action in the game."""
        try:
            session = await self.get_session(session_id)
            if not session:
                raise Exception(f"Session not found: {session_id}")
            
            # Send action to game
            game_response = await self.game_interface.send_action(session.game_id, action)
            
            # Create response object
            response = ActionResponse(
                response=game_response.get("response", ""),
                game_state=game_response.get("game_state", ""),
                action_successful=game_response.get("action_successful", True),
                game_completed=game_response.get("game_completed", False)
            )
            
            # Update session
            session.current_state = response.game_state
            session.path_history.append({
                "action": action,
                "response": response.response,
                "game_state": response.game_state,
                "successful": response.action_successful
            })
            
            # Save action to database
            await self.database.add_action(
                session_id=session_id,
                action=action,
                game_response=response.response,
                game_state=response.game_state,
                action_successful=response.action_successful
            )
            
            # Update session status if game completed
            if response.game_completed:
                session.status = "completed"
                await self.game_interface.end_game(session.game_id)
            
            # Save session
            await self._save_session(session)
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            raise
    
    async def play_game_autonomously(self, session_id: str, max_actions: int = 100):
        """Play the game autonomously using the LLM."""
        try:
            session = await self.get_session(session_id)
            if not session:
                raise Exception(f"Session not found: {session_id}")
            
            logger.info(f"Starting autonomous gameplay for session: {session_id}")
            
            action_count = 0
            while action_count < max_actions and session.status == "active":
                # Get previous actions for context
                previous_actions = [step["action"] for step in session.path_history[-10:]]
                
                # Analyze current state and get suggested action
                analysis = await self.llm_service.analyze_game_state(
                    session.current_state, 
                    previous_actions
                )
                
                suggested_action = analysis.get("suggested_action", "look")
                
                # Execute the action
                response = await self.execute_action(session_id, suggested_action)
                
                logger.info(f"Action {action_count + 1}: {suggested_action} -> {response.response[:100]}...")
                
                # Check if game is completed
                if response.game_completed:
                    logger.info(f"Game completed for session: {session_id}")
                    break
                
                action_count += 1
                
                # Small delay between actions
                await asyncio.sleep(1)
            
            logger.info(f"Autonomous gameplay finished for session: {session_id} after {action_count} actions")
            
        except Exception as e:
            logger.error(f"Error in autonomous gameplay: {e}")
            raise
    
    async def get_game_path(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the path taken through the game."""
        session = await self.get_session(session_id)
        if session:
            return session.path_history
        return []
    
    async def delete_session(self, session_id: str):
        """Delete a game session."""
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await self.game_interface.end_game(session.game_id)
                del self.active_sessions[session_id]
            
            # Delete from database
            await self.database.delete_session(session_id)
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get AI agent statistics."""
        return await self.database.get_stats()
    
    async def reset(self):
        """Reset the AI agent (clear all sessions)."""
        try:
            # End all active games
            for session in self.active_sessions.values():
                await self.game_interface.end_game(session.game_id)
            
            # Clear active sessions
            self.active_sessions = {}
            
            # Reset database
            await self.database.reset_all()
            
            logger.info("AI Agent reset complete")
            
        except Exception as e:
            logger.error(f"Error resetting agent: {e}")
            raise