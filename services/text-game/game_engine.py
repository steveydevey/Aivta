"""
Simple text-based adventure game engine.
"""

import uuid
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from config import Settings


@dataclass
class Room:
    """Room in the game world."""
    name: str
    description: str
    exits: Dict[str, str]  # direction -> room_name
    items: List[str]
    visited: bool = False


@dataclass
class Item:
    """Item that can be picked up."""
    name: str
    description: str
    portable: bool = True
    use_message: str = ""


@dataclass
class Player:
    """Player state."""
    current_room: str
    inventory: List[str]
    score: int = 0
    moves: int = 0


@dataclass
class GameSession:
    """Game session data."""
    session_id: str
    game_type: str
    status: str
    created_at: str
    last_action: Optional[str] = None
    player: Optional[Player] = None


class AdventureGame:
    """Simple adventure game engine."""
    
    def __init__(self):
        self.settings = Settings()
        self.sessions: Dict[str, GameSession] = {}
        self.rooms: Dict[str, Room] = {}
        self.items: Dict[str, Item] = {}
        self.game_initialized = False
    
    async def initialize(self):
        """Initialize the game world."""
        if self.game_initialized:
            return
        
        # Create basic game world
        self._create_game_world()
        
        # Create saves directory
        os.makedirs(self.settings.saves_dir, exist_ok=True)
        
        self.game_initialized = True
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        # Save all active sessions
        for session_id in list(self.sessions.keys()):
            try:
                await self.save_game(session_id)
            except Exception as e:
                print(f"Error saving session {session_id}: {e}")
    
    def _create_game_world(self):
        """Create the basic game world."""
        # Create rooms
        self.rooms = {
            "start": Room(
                name="Forest Clearing",
                description="You are in a small clearing in a dark forest. Tall trees surround you on all sides. There is a path leading north to what appears to be a cave entrance.",
                exits={"north": "cave_entrance", "east": "forest_path"},
                items=["stick"]
            ),
            "cave_entrance": Room(
                name="Cave Entrance",
                description="You stand before a dark cave entrance. The opening is large enough to walk through, but you can't see what lies beyond. A cold breeze flows from within.",
                exits={"south": "start", "north": "cave_interior"},
                items=["torch"]
            ),
            "cave_interior": Room(
                name="Cave Interior",
                description="Inside the cave, your torch illuminates rough stone walls. You can hear the sound of dripping water echoing from deeper within. There's a passage leading further north.",
                exits={"south": "cave_entrance", "north": "treasure_room"},
                items=[]
            ),
            "treasure_room": Room(
                name="Treasure Room",
                description="You've discovered a small chamber filled with ancient treasures! Gold coins glitter in the torchlight, and there's an ornate chest in the center of the room.",
                exits={"south": "cave_interior"},
                items=["gold_coins", "treasure_chest"]
            ),
            "forest_path": Room(
                name="Forest Path",
                description="A winding path through the forest. The trees are less dense here, and you can see sunlight filtering through the canopy above.",
                exits={"west": "start", "east": "forest_exit"},
                items=["berries"]
            ),
            "forest_exit": Room(
                name="Forest Exit",
                description="You've reached the edge of the forest. Beyond lies a vast open plain stretching to the horizon. You've successfully navigated the forest!",
                exits={"west": "forest_path"},
                items=[]
            )
        }
        
        # Create items
        self.items = {
            "stick": Item(
                name="stick",
                description="A sturdy wooden stick. It might be useful as a tool or weapon.",
                portable=True,
                use_message="You wave the stick around. It's quite sturdy!"
            ),
            "torch": Item(
                name="torch",
                description="A burning torch that provides light in dark places.",
                portable=True,
                use_message="The torch burns brightly, illuminating your surroundings."
            ),
            "gold_coins": Item(
                name="gold coins",
                description="A handful of ancient gold coins. They're quite valuable!",
                portable=True,
                use_message="The gold coins jingle pleasantly in your hands."
            ),
            "treasure_chest": Item(
                name="treasure chest",
                description="An ornate wooden chest bound with iron. It's locked, but perhaps you could open it...",
                portable=False,
                use_message="The chest is locked tight. You need a key to open it."
            ),
            "berries": Item(
                name="berries",
                description="Sweet forest berries. They look safe to eat.",
                portable=True,
                use_message="You eat the berries. They're delicious and restore your energy!"
            )
        }
    
    async def create_session(self, game_type: str = "adventure") -> GameSession:
        """Create a new game session."""
        session_id = str(uuid.uuid4())
        
        session = GameSession(
            session_id=session_id,
            game_type=game_type,
            status="active",
            created_at=datetime.now().isoformat(),
            player=Player(
                current_room="start",
                inventory=[],
                score=0,
                moves=0
            )
        )
        
        self.sessions[session_id] = session
        return session
    
    async def get_game_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        return {
            "session_id": session_id,
            "current_location": current_room.name,
            "description": current_room.description,
            "inventory": player.inventory,
            "score": player.score,
            "moves": player.moves,
            "game_over": session.status == "completed",
            "victory": session.status == "won"
        }
    
    async def execute_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Execute a game command."""
        if session_id not in self.sessions:
            return {
                "response": "Session not found.",
                "game_state": {},
                "valid_commands": [],
                "error": "Session not found"
            }
        
        session = self.sessions[session_id]
        player = session.player
        
        if session.status != "active":
            return {
                "response": "Game is not active.",
                "game_state": await self.get_game_state(session_id),
                "valid_commands": [],
                "error": "Game not active"
            }
        
        # Parse command
        command = command.lower().strip()
        parts = command.split()
        
        if not parts:
            return {
                "response": "Please enter a command.",
                "game_state": await self.get_game_state(session_id),
                "valid_commands": await self.get_valid_commands(session_id),
                "error": "Empty command"
            }
        
        verb = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Execute command
        response = await self._execute_verb(session_id, verb, args)
        
        # Update move counter
        player.moves += 1
        session.last_action = command
        
        # Check win condition
        if player.current_room == "forest_exit":
            session.status = "won"
            player.score += 100
            response += "\n\nCongratulations! You've successfully completed the adventure!"
        
        return {
            "response": response,
            "game_state": await self.get_game_state(session_id),
            "valid_commands": await self.get_valid_commands(session_id),
            "error": None
        }
    
    async def _execute_verb(self, session_id: str, verb: str, args: List[str]) -> str:
        """Execute a specific verb command."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        # Movement commands
        if verb in ["go", "move", "walk"] and args:
            direction = args[0]
            return await self._move_player(session_id, direction)
        elif verb in ["north", "south", "east", "west", "n", "s", "e", "w"]:
            direction_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            direction = direction_map.get(verb, verb)
            return await self._move_player(session_id, direction)
        
        # Look commands
        elif verb in ["look", "examine", "l"]:
            if args:
                target = " ".join(args)
                return await self._examine_object(session_id, target)
            else:
                return await self._look_around(session_id)
        
        # Inventory commands
        elif verb in ["inventory", "i"]:
            return await self._show_inventory(session_id)
        
        # Take/get commands
        elif verb in ["take", "get", "pick"]:
            if args:
                item = " ".join(args)
                return await self._take_item(session_id, item)
            else:
                return "Take what?"
        
        # Drop commands
        elif verb in ["drop", "put"]:
            if args:
                item = " ".join(args)
                return await self._drop_item(session_id, item)
            else:
                return "Drop what?"
        
        # Use commands
        elif verb in ["use", "activate"]:
            if args:
                item = " ".join(args)
                return await self._use_item(session_id, item)
            else:
                return "Use what?"
        
        # Help command
        elif verb in ["help", "?"]:
            return await self._show_help()
        
        # Unknown command
        else:
            return f"I don't understand '{verb}'. Type 'help' for a list of commands."
    
    async def _move_player(self, session_id: str, direction: str) -> str:
        """Move player in a direction."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        if direction not in current_room.exits:
            return f"You can't go {direction} from here."
        
        new_room_name = current_room.exits[direction]
        new_room = self.rooms[new_room_name]
        
        player.current_room = new_room_name
        player.score += 5  # Points for exploration
        
        # Mark room as visited
        new_room.visited = True
        
        response = f"You go {direction}.\n\n"
        response += await self._look_around(session_id)
        
        return response
    
    async def _look_around(self, session_id: str) -> str:
        """Look around the current room."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        response = f"{current_room.name}\n{current_room.description}"
        
        # Show items
        if current_room.items:
            response += "\n\nYou can see: " + ", ".join(current_room.items)
        
        # Show exits
        if current_room.exits:
            exits = list(current_room.exits.keys())
            response += f"\n\nExits: {', '.join(exits)}"
        
        return response
    
    async def _examine_object(self, session_id: str, target: str) -> str:
        """Examine an object."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        # Check if target is in room or inventory
        if target in current_room.items or target in player.inventory:
            if target in self.items:
                return self.items[target].description
            else:
                return f"You see nothing special about the {target}."
        
        return f"You don't see a {target} here."
    
    async def _take_item(self, session_id: str, item_name: str) -> str:
        """Take an item."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        if item_name not in current_room.items:
            return f"You don't see a {item_name} here."
        
        if item_name in self.items and not self.items[item_name].portable:
            return f"You can't take the {item_name}."
        
        # Move item from room to inventory
        current_room.items.remove(item_name)
        player.inventory.append(item_name)
        player.score += 10  # Points for finding items
        
        return f"You take the {item_name}."
    
    async def _drop_item(self, session_id: str, item_name: str) -> str:
        """Drop an item."""
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        if item_name not in player.inventory:
            return f"You don't have a {item_name}."
        
        # Move item from inventory to room
        player.inventory.remove(item_name)
        current_room.items.append(item_name)
        
        return f"You drop the {item_name}."
    
    async def _use_item(self, session_id: str, item_name: str) -> str:
        """Use an item."""
        session = self.sessions[session_id]
        player = session.player
        
        if item_name not in player.inventory:
            return f"You don't have a {item_name}."
        
        if item_name in self.items:
            return self.items[item_name].use_message
        
        return f"You can't use the {item_name}."
    
    async def _show_inventory(self, session_id: str) -> str:
        """Show player inventory."""
        session = self.sessions[session_id]
        player = session.player
        
        if not player.inventory:
            return "You are carrying nothing."
        
        return "You are carrying: " + ", ".join(player.inventory)
    
    async def _show_help(self) -> str:
        """Show help message."""
        return """Available commands:
        - go [direction] / [direction] - Move in a direction (north, south, east, west)
        - look / examine [object] - Look around or examine something
        - take [item] - Pick up an item
        - drop [item] - Drop an item
        - use [item] - Use an item
        - inventory / i - Show your inventory
        - help / ? - Show this help message
        
        Common directions: north (n), south (s), east (e), west (w)
        """
    
    async def get_valid_commands(self, session_id: str) -> List[str]:
        """Get valid commands for current state."""
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        player = session.player
        current_room = self.rooms[player.current_room]
        
        commands = ["look", "inventory", "help"]
        
        # Add movement commands
        for direction in current_room.exits.keys():
            commands.append(f"go {direction}")
            commands.append(direction)
        
        # Add item commands
        for item in current_room.items:
            commands.append(f"take {item}")
            commands.append(f"examine {item}")
        
        for item in player.inventory:
            commands.append(f"drop {item}")
            commands.append(f"use {item}")
            commands.append(f"examine {item}")
        
        return commands
    
    async def get_active_sessions_count(self) -> int:
        """Get number of active sessions."""
        return len([s for s in self.sessions.values() if s.status == "active"])
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        return [asdict(session) for session in self.sessions.values()]
    
    async def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    async def save_game(self, session_id: str) -> str:
        """Save game to file."""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        
        session = self.sessions[session_id]
        filename = f"save_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.settings.saves_dir, filename)
        
        save_data = {
            "session": asdict(session),
            "rooms": {name: asdict(room) for name, room in self.rooms.items()},
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return filename
    
    async def load_game(self, session_id: str, filename: str):
        """Load game from file."""
        filepath = os.path.join(self.settings.saves_dir, filename)
        
        if not os.path.exists(filepath):
            raise ValueError("Save file not found")
        
        with open(filepath, 'r') as f:
            save_data = json.load(f)
        
        # Restore session
        session_data = save_data["session"]
        session = GameSession(**session_data)
        session.player = Player(**session_data["player"])
        
        self.sessions[session_id] = session
        
        # Restore room states
        for name, room_data in save_data["rooms"].items():
            if name in self.rooms:
                self.rooms[name].visited = room_data.get("visited", False)
                self.rooms[name].items = room_data.get("items", [])
    
    async def get_game_info(self) -> Dict[str, Any]:
        """Get game information."""
        return {
            "name": "Simple Adventure",
            "version": "1.0.0",
            "description": "A simple text-based adventure game",
            "total_rooms": len(self.rooms),
            "total_items": len(self.items),
            "active_sessions": await self.get_active_sessions_count()
        }