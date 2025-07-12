"""
Configuration settings for the text game service.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the text game service."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Game settings
    game_type: str = "adventure"
    max_sessions: int = 100
    session_timeout: int = 3600  # 1 hour
    
    # File paths
    saves_dir: str = "saves"
    game_data_dir: str = "game_data"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False