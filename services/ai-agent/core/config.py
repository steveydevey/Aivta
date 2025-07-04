"""Configuration management for the AI Agent service."""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://aivta_user:aivta_password@database:5432/aivta",
        env="DATABASE_URL"
    )
    
    # LLM configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ollama_host: str = Field(default="http://ollama:11434", env="OLLAMA_HOST")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    
    # Game configuration
    text_game_host: str = Field(default="text-game", env="TEXT_GAME_HOST")
    text_game_port: int = Field(default=8080, env="TEXT_GAME_PORT")
    
    # Agent configuration
    max_actions_per_game: int = Field(default=1000, env="MAX_ACTIONS_PER_GAME")
    max_context_length: int = Field(default=4000, env="MAX_CONTEXT_LENGTH")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Development settings
    debug: bool = Field(default=False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        case_sensitive = False