"""
Tests for text game service.
"""

import pytest
import requests
import time
import subprocess
import os


class TestTextGameService:
    """Test class for text game service."""
    
    @pytest.fixture(autouse=True)
    def setup_game_service(self):
        """Set up the text game service for testing."""
        # Start the text game service
        self.game_process = None
        self.base_url = "http://localhost:8080"
        
        try:
            # Change to the text game service directory
            os.chdir("services/text-game")
            
            # Start the service
            self.game_process = subprocess.Popen(
                ["python", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for service to start
            time.sleep(3)
            
            yield
            
        finally:
            # Clean up
            if self.game_process:
                self.game_process.terminate()
                self.game_process.wait()
            
            # Change back to workspace root
            os.chdir("../..")
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "text-game"
    
    def test_get_game_state(self):
        """Test getting initial game state."""
        response = requests.get(f"{self.base_url}/game/state")
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "location" in data
        assert "available_actions" in data
        assert "inventory" in data
        assert "score" in data
        
        # Check initial state
        assert data["location"] == "entrance"
        assert data["score"] == 0
        assert "torch" in data["available_actions"]
    
    def test_move_command(self):
        """Test moving between locations."""
        # Move north
        response = requests.post(
            f"{self.base_url}/game/command",
            json={"command": "go north"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "You moved north" in data["response"]
        assert data["location"] == "chamber"
        assert "key" in data["available_actions"]
    
    def test_take_command(self):
        """Test taking items."""
        # Take the torch
        response = requests.post(
            f"{self.base_url}/game/command",
            json={"command": "take torch"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "You picked up the torch" in data["response"]
        assert "torch" in data["inventory"]
        assert data["score"] == 10
        assert "take torch" not in data["available_actions"]
    
    def test_look_around_command(self):
        """Test look around command."""
        response = requests.post(
            f"{self.base_url}/game/command",
            json={"command": "look around"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "entrance of a mysterious cave" in data["response"]
    
    def test_inventory_command(self):
        """Test inventory command."""
        # First take an item
        requests.post(
            f"{self.base_url}/game/command",
            json={"command": "take torch"}
        )
        
        # Check inventory
        response = requests.post(
            f"{self.base_url}/game/command",
            json={"command": "inventory"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "torch" in data["response"]
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        response = requests.post(
            f"{self.base_url}/game/command",
            json={"command": "invalid command"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "I don't understand" in data["response"]
    
    def test_reset_game(self):
        """Test game reset functionality."""
        # First move and take an item
        requests.post(
            f"{self.base_url}/game/command",
            json={"command": "go north"}
        )
        requests.post(
            f"{self.base_url}/game/command",
            json={"command": "take key"}
        )
        
        # Reset the game
        response = requests.post(f"{self.base_url}/game/reset")
        assert response.status_code == 200
        data = response.json()
        assert "reset successfully" in data["message"]
        
        # Check that game is back to initial state
        state_response = requests.get(f"{self.base_url}/game/state")
        state_data = state_response.json()
        
        assert state_data["location"] == "entrance"
        assert state_data["score"] == 0
        assert state_data["inventory"] == []
        assert "torch" in state_data["available_actions"]


# Skip these tests if requests is not available or if we can't start the service
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("requests"),
    reason="requests library not available"
)