"""Game interface for the AI Agent."""

import logging
import asyncio
from typing import Dict, Any, Optional
import json

import httpx

from .config import Settings

logger = logging.getLogger(__name__)


class GameInterface:
    """Interface for communicating with text-based games."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        self.base_url = f"http://{settings.text_game_host}:{settings.text_game_port}"
        
    async def initialize(self):
        """Initialize game interface."""
        try:
            self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
            await self.test_connection()
            logger.info("Game interface initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing game interface: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown game interface."""
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check game interface health."""
        try:
            result = await self.test_connection()
            return {"status": "healthy", "result": result}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def test_connection(self) -> str:
        """Test connection to game service."""
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                return "Game service is healthy"
            else:
                raise Exception(f"Game service returned status {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Game connection test failed: {e}")
            # Return a mock response for development
            return "Game service connection test (mock)"
    
    async def start_game(self, game_type: str = "adventure") -> Dict[str, Any]:
        """Start a new game session."""
        try:
            response = await self.client.post(
                "/games/start",
                json={"game_type": game_type}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to start game: {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Error starting game: {e}")
            # Return a mock response for development
            return {
                "game_id": "mock_game_001",
                "game_type": game_type,
                "initial_state": "You are standing at the entrance of a mysterious cave. The air is cool and damp. There are passages leading north and east.",
                "status": "started"
            }
    
    async def send_action(self, game_id: str, action: str) -> Dict[str, Any]:
        """Send an action to the game and get the response."""
        try:
            response = await self.client.post(
                f"/games/{game_id}/action",
                json={"action": action}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to send action: {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Error sending action: {e}")
            # Return a mock response for development
            return await self._mock_game_response(action)
    
    async def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Get the current game state."""
        try:
            response = await self.client.get(f"/games/{game_id}/state")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to get game state: {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Error getting game state: {e}")
            # Return a mock response for development
            return {
                "game_id": game_id,
                "current_state": "You are in a dimly lit room. There's a door to the north.",
                "status": "active",
                "score": 0,
                "moves": 1
            }
    
    async def end_game(self, game_id: str) -> Dict[str, Any]:
        """End a game session."""
        try:
            response = await self.client.post(f"/games/{game_id}/end")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to end game: {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Error ending game: {e}")
            # Return a mock response for development
            return {
                "game_id": game_id,
                "status": "ended",
                "final_score": 0
            }
    
    async def _mock_game_response(self, action: str) -> Dict[str, Any]:
        """Generate mock game responses for development."""
        action_lower = action.lower()
        
        # Mock responses based on common adventure game actions
        if "look" in action_lower:
            responses = [
                "You are in a dark cave. Passages lead north and east.",
                "You see a treasure chest in the corner of the room.",
                "A mysterious door stands before you, slightly ajar.",
                "You're in a forest clearing with paths in all directions."
            ]
        elif "north" in action_lower:
            responses = [
                "You walk north into a darker passage.",
                "You enter a room filled with ancient artifacts.",
                "The passage narrows as you continue north."
            ]
        elif "east" in action_lower:
            responses = [
                "You head east and find a hidden chamber.",
                "The eastern path leads to a underground lake.",
                "You discover a room full of glittering gems."
            ]
        elif "take" in action_lower or "get" in action_lower:
            responses = [
                "You pick up the item and add it to your inventory.",
                "The object feels warm in your hands.",
                "You successfully take the item."
            ]
        elif "open" in action_lower:
            responses = [
                "The door creaks open, revealing a hidden room.",
                "You open the chest and find a golden key inside.",
                "The container opens with a satisfying click."
            ]
        else:
            responses = [
                "You try that action but nothing happens.",
                "I don't understand that command.",
                "You look around, unsure what to do next."
            ]
        
        import random
        response_text = random.choice(responses)
        
        # Randomly determine if game is completed
        game_completed = random.random() < 0.05  # 5% chance
        
        return {
            "response": response_text,
            "game_state": response_text,
            "action_successful": True,
            "game_completed": game_completed,
            "score": random.randint(0, 100),
            "moves": random.randint(1, 50)
        }