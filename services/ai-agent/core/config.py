"""Configuration management for the AI Agent service."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://aivta_user:aivta_password@database:5432/aivta"
    )
    
    # LLM configuration
    openai_api_key: Optional[str] = Field(default=None)
    ollama_host: str = Field(default="http://ollama:11434")
    llm_model: str = Field(default="gpt-3.5-turbo")
    
    # Game configuration
    text_game_host: str = Field(default="text-game")
    text_game_port: int = Field(default=8080)
    
    # Agent configuration
    max_actions_per_game: int = Field(default=1000)
    max_context_length: int = Field(default=4000)
    
    # Logging configuration
    log_level: str = Field(default="INFO")
    
    # Development settings
    debug: bool = Field(default=False)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }