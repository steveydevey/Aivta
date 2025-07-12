"""
Test suite for the AI Agent service.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Import the main application
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))

from main import app


class TestAIAgent:
    """Test cases for AI Agent service."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-agent"
    
    def test_create_session(self):
        """Test creating a new game session."""
        response = self.client.post("/sessions", params={"game_type": "adventure"})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["game_type"] == "adventure"
        assert data["status"] == "active"
    
    def test_get_session(self):
        """Test retrieving a game session."""
        # First create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Then retrieve it
        response = self.client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
    
    def test_get_nonexistent_session(self):
        """Test retrieving a nonexistent session."""
        response = self.client.get("/sessions/nonexistent-id")
        assert response.status_code == 404
    
    def test_execute_action(self):
        """Test executing an action in a game session."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Execute an action
        action_data = {
            "session_id": session_id,
            "action": "look around",
            "context": "starting the game"
        }
        response = self.client.post(f"/sessions/{session_id}/actions", json=action_data)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "response" in data
        assert "game_state" in data
    
    def test_get_agent_stats(self):
        """Test getting agent statistics."""
        response = self.client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "completed_games" in data
    
    def test_reset_agent(self):
        """Test resetting the agent."""
        response = self.client.post("/reset")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
class TestAIAgentAsync:
    """Async test cases for AI Agent service."""
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_health_check_async(self, async_client):
        """Test health check endpoint asynchronously."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_create_multiple_sessions(self, async_client):
        """Test creating multiple sessions concurrently."""
        tasks = []
        for i in range(5):
            task = async_client.post("/sessions", params={"game_type": "adventure"})
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        session_ids = set()
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            session_ids.add(data["session_id"])
        
        # Ensure all session IDs are unique
        assert len(session_ids) == 5


class TestAIAgentIntegration:
    """Integration tests for AI Agent service."""
    
    def setup_method(self):
        """Setup integration test fixtures."""
        self.client = TestClient(app)
    
    def test_full_game_workflow(self):
        """Test a complete game workflow."""
        # 1. Create a session
        create_response = self.client.post("/sessions")
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]
        
        # 2. Get initial session state
        state_response = self.client.get(f"/sessions/{session_id}")
        assert state_response.status_code == 200
        
        # 3. Execute a series of actions
        actions = ["look around", "go north", "examine torch"]
        for action in actions:
            action_data = {
                "session_id": session_id,
                "action": action
            }
            response = self.client.post(f"/sessions/{session_id}/actions", json=action_data)
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
        
        # 4. Get game path
        path_response = self.client.get(f"/sessions/{session_id}/path")
        assert path_response.status_code == 200
        path_data = path_response.json()
        assert "path" in path_data
        
        # 5. Delete session
        delete_response = self.client.delete(f"/sessions/{session_id}")
        assert delete_response.status_code == 200
    
    def test_autonomous_gameplay(self):
        """Test starting autonomous gameplay."""
        # Create a session
        create_response = self.client.post("/sessions")
        session_id = create_response.json()["session_id"]
        
        # Start autonomous play
        response = self.client.post(f"/sessions/{session_id}/play")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])