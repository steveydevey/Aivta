"""
Aivta Text Game Service
Simple text-based adventure game for testing AI agent integration.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple game state
class GameState:
    def __init__(self):
        self.location = "entrance"
        self.inventory = []
        self.score = 0
        self.game_map = {
            "entrance": {
                "description": "You are at the entrance of a mysterious cave. Paths lead north and east.",
                "exits": {"north": "chamber", "east": "tunnel"},
                "items": ["torch"]
            },
            "chamber": {
                "description": "You are in a dark chamber. There's a key on the ground. Paths lead south and west.",
                "exits": {"south": "entrance", "west": "treasure_room"},
                "items": ["key"]
            },
            "tunnel": {
                "description": "You are in a narrow tunnel. It's very dark here. Paths lead west and north.",
                "exits": {"west": "entrance", "north": "treasure_room"},
                "items": []
            },
            "treasure_room": {
                "description": "You've found the treasure room! There's gold everywhere! Paths lead east and south.",
                "exits": {"east": "chamber", "south": "tunnel"},
                "items": ["gold", "crown"]
            }
        }
    
    def get_current_description(self) -> str:
        room = self.game_map[self.location]
        desc = room["description"]
        if room["items"]:
            desc += f" You can see: {', '.join(room['items'])}"
        return desc
    
    def get_available_actions(self) -> list:
        room = self.game_map[self.location]
        actions = [f"go {direction}" for direction in room["exits"].keys()]
        actions.extend([f"take {item}" for item in room["items"]])
        actions.append("look around")
        actions.append("inventory")
        return actions

# Global game state
game_state = GameState()

# FastAPI app
app = FastAPI(
    title="Aivta Text Game",
    description="Simple text adventure game for AI agent testing",
    version="1.0.0"
)

# Pydantic models
class GameCommand(BaseModel):
    command: str = Field(..., description="Game command to execute")

class GameResponse(BaseModel):
    response: str = Field(..., description="Game response")
    location: str = Field(..., description="Current location")
    available_actions: list = Field(..., description="Available actions")
    inventory: list = Field(..., description="Current inventory")
    score: int = Field(..., description="Current score")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "text-game"}

@app.get("/game/state")
async def get_game_state():
    """Get current game state."""
    return GameResponse(
        response=game_state.get_current_description(),
        location=game_state.location,
        available_actions=game_state.get_available_actions(),
        inventory=game_state.inventory,
        score=game_state.score
    )

@app.post("/game/command")
async def execute_command(command: GameCommand):
    """Execute a game command."""
    cmd = command.command.lower().strip()
    
    try:
        if cmd.startswith("go "):
            direction = cmd[3:]
            if direction in game_state.game_map[game_state.location]["exits"]:
                game_state.location = game_state.game_map[game_state.location]["exits"][direction]
                response = f"You moved {direction}. {game_state.get_current_description()}"
            else:
                response = f"You can't go {direction} from here."
        
        elif cmd.startswith("take "):
            item = cmd[5:]
            room = game_state.game_map[game_state.location]
            if item in room["items"]:
                room["items"].remove(item)
                game_state.inventory.append(item)
                game_state.score += 10
                response = f"You picked up the {item}."
            else:
                response = f"There's no {item} here."
        
        elif cmd == "look around":
            response = game_state.get_current_description()
        
        elif cmd == "inventory":
            if game_state.inventory:
                response = f"You are carrying: {', '.join(game_state.inventory)}"
            else:
                response = "You are not carrying anything."
        
        else:
            response = f"I don't understand '{cmd}'. Try: {', '.join(game_state.get_available_actions()[:3])}"
        
        return GameResponse(
            response=response,
            location=game_state.location,
            available_actions=game_state.get_available_actions(),
            inventory=game_state.inventory,
            score=game_state.score
        )
    
    except Exception as e:
        logger.error(f"Error executing command '{cmd}': {e}")
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")

@app.post("/game/reset")
async def reset_game():
    """Reset the game to initial state."""
    global game_state
    game_state = GameState()
    return {"message": "Game reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)