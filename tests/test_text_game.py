"""
Test suite for the Text Game service.
"""

import pytest
from fastapi.testclient import TestClient

# Import the main application
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'text-game'))

from main import app


class TestTextGame:
    """Test cases for Text Game service."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "text-game"
    
    def test_create_session(self):
        """Test creating a new game session."""
        response = self.client.post("/sessions", params={"game_type": "adventure"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["game_type"] == "adventure"
        assert data["status"] == "active"
    
    def test_get_session_state(self):
        """Test getting game state for a session."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Get session state
        response = self.client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "current_location" in data
        assert "description" in data
        assert "inventory" in data
    
    def test_execute_command(self):
        """Test executing a command in the game."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Execute a command
        command_data = {
            "session_id": session_id,
            "command": "look"
        }
        response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "response" in data
        assert "game_state" in data
    
    def test_get_valid_commands(self):
        """Test getting valid commands for a session."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Get valid commands
        response = self.client.get(f"/sessions/{session_id}/valid-commands")
        assert response.status_code == 200
        data = response.json()
        assert "valid_commands" in data
        assert isinstance(data["valid_commands"], list)
    
    def test_game_info(self):
        """Test getting game information."""
        response = self.client.get("/game-info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
    
    def test_list_sessions(self):
        """Test listing all sessions."""
        response = self.client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)


class TestGameplayMechanics:
    """Test game mechanics and gameplay."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
    
    def test_movement_commands(self):
        """Test movement commands."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Test movement
        commands = ["north", "go north", "move north", "n"]
        for command in commands:
            command_data = {
                "session_id": session_id,
                "command": command
            }
            response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            # Note: Some commands might fail (e.g., if already moved), but they should still return 200
    
    def test_inventory_commands(self):
        """Test inventory-related commands."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Test inventory commands
        commands = ["inventory", "i", "take stick", "drop stick"]
        for command in commands:
            command_data = {
                "session_id": session_id,
                "command": command
            }
            response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
    
    def test_examination_commands(self):
        """Test examination commands."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Test examination commands
        commands = ["look", "examine stick", "look around"]
        for command in commands:
            command_data = {
                "session_id": session_id,
                "command": command
            }
            response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
    
    def test_help_command(self):
        """Test help command."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Test help command
        command_data = {
            "session_id": session_id,
            "command": "help"
        }
        response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
        assert response.status_code == 200
        data = response.json()
        assert "Available commands" in data["response"]
    
    def test_game_progression(self):
        """Test game progression through multiple rooms."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Progress through the game
        commands = [
            "look",
            "take stick",
            "north",
            "take torch",
            "north",
            "north",
            "take gold coins",
            "south",
            "south",
            "south",
            "east",
            "take berries",
            "east"
        ]
        
        for command in commands:
            command_data = {
                "session_id": session_id,
                "command": command
            }
            response = self.client.post(f"/sessions/{session_id}/commands", json=command_data)
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            
            # Check if game is won
            if data["game_state"]["victory"]:
                assert "Congratulations" in data["response"]
                break


class TestGameSaveLoad:
    """Test game save and load functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
    
    def test_save_game(self):
        """Test saving a game."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Make some progress
        command_data = {
            "session_id": session_id,
            "command": "take stick"
        }
        self.client.post(f"/sessions/{session_id}/commands", json=command_data)
        
        # Save the game
        response = self.client.post(f"/sessions/{session_id}/save")
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "message" in data
    
    def test_load_game(self):
        """Test loading a game (mock test since we need an actual save file)."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Try to load a nonexistent file (should fail gracefully)
        response = self.client.post(f"/sessions/{session_id}/load", params={"filename": "nonexistent.json"})
        assert response.status_code == 500  # Should fail for nonexistent file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])