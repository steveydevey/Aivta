"""Database management for the AI Agent service."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

import asyncpg
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class Database:
    """Database manager for the AI Agent service."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.pool = None
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(self.database_url)
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown database connections."""
        if self.pool:
            await self.pool.close()
            
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            if not self.pool:
                return {"status": "unhealthy", "error": "No connection pool"}
                
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return {"status": "healthy", "result": result}
                
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def _create_tables(self):
        """Create database tables."""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id VARCHAR(36) PRIMARY KEY,
            game_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            current_state TEXT,
            path_history JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS game_actions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            action TEXT NOT NULL,
            game_response TEXT,
            game_state TEXT,
            action_successful BOOLEAN DEFAULT TRUE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
        );
        
        CREATE TABLE IF NOT EXISTS agent_stats (
            id SERIAL PRIMARY KEY,
            metric_name VARCHAR(50) NOT NULL,
            metric_value FLOAT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_game_actions_session_id ON game_actions(session_id);
        CREATE INDEX IF NOT EXISTS idx_agent_stats_timestamp ON agent_stats(timestamp);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_tables_sql)
    
    async def create_session(self, game_type: str) -> str:
        """Create a new game session."""
        session_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO game_sessions (session_id, game_type) VALUES ($1, $2)",
                session_id, game_type
            )
            
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get game session details."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM game_sessions WHERE session_id = $1",
                session_id
            )
            
            if row:
                return dict(row)
            return None
    
    async def update_session(self, session_id: str, **kwargs):
        """Update game session."""
        if not kwargs:
            return
            
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = [session_id] + list(kwargs.values())
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE game_sessions SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE session_id = $1",
                *values
            )
    
    async def add_action(self, session_id: str, action: str, game_response: str, 
                        game_state: str, action_successful: bool = True):
        """Add a game action to the database."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO game_actions 
                   (session_id, action, game_response, game_state, action_successful) 
                   VALUES ($1, $2, $3, $4, $5)""",
                session_id, action, game_response, game_state, action_successful
            )
    
    async def get_session_actions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all actions for a session."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM game_actions WHERE session_id = $1 ORDER BY timestamp",
                session_id
            )
            
            return [dict(row) for row in rows]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        async with self.pool.acquire() as conn:
            # Get session counts
            total_sessions = await conn.fetchval(
                "SELECT COUNT(*) FROM game_sessions"
            )
            
            active_sessions = await conn.fetchval(
                "SELECT COUNT(*) FROM game_sessions WHERE status = 'active'"
            )
            
            completed_games = await conn.fetchval(
                "SELECT COUNT(*) FROM game_sessions WHERE status = 'completed'"
            )
            
            # Calculate success rate
            success_rate = 0.0
            if total_sessions > 0:
                success_rate = completed_games / total_sessions
            
            # Calculate average actions per game
            avg_actions = await conn.fetchval(
                """SELECT AVG(action_count) FROM (
                    SELECT COUNT(*) as action_count 
                    FROM game_actions 
                    GROUP BY session_id
                ) as action_counts"""
            ) or 0.0
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "completed_games": completed_games,
                "success_rate": success_rate,
                "average_actions_per_game": float(avg_actions)
            }
    
    async def delete_session(self, session_id: str):
        """Delete a game session and its actions."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM game_actions WHERE session_id = $1",
                    session_id
                )
                await conn.execute(
                    "DELETE FROM game_sessions WHERE session_id = $1",
                    session_id
                )
    
    async def reset_all(self):
        """Reset all data (for testing/debugging)."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM game_actions")
                await conn.execute("DELETE FROM game_sessions")
                await conn.execute("DELETE FROM agent_stats")