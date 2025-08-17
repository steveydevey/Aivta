"""
Simplified tests for text game service.
"""

import pytest
import requests
import time
import subprocess
import os


class TestTextGameServiceSimple:
    """Simplified test class for text game service."""
    
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
        assert "take torch" in data["available_actions"]
    
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
        assert "take key" in data["available_actions"]


# Skip these tests if requests is not available
pytestmark = pytest.mark.skipif(
    not pytest.importorskip("requests"),
    reason="requests library not available"
)