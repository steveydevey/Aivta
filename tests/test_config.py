"""
Tests for configuration module.
"""

import pytest
from core.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    
    assert settings.database_url == "postgresql://aivta_user:aivta_password@database:5432/aivta"
    assert settings.openai_api_key is None
    assert settings.ollama_host == "http://ollama:11434"
    assert settings.text_game_host == "text-game"
    assert settings.text_game_port == 8080
    assert settings.log_level == "INFO"


def test_settings_custom_values():
    """Test that settings can be customized."""
    custom_settings = Settings(
        database_url="postgresql://custom:pass@localhost:5432/custom_db",
        openai_api_key="custom_key",
        ollama_host="http://localhost:11434",
        text_game_host="localhost",
        text_game_port=9000,
        log_level="DEBUG"
    )
    
    assert custom_settings.database_url == "postgresql://custom:pass@localhost:5432/custom_db"
    assert custom_settings.openai_api_key == "custom_key"
    assert custom_settings.ollama_host == "http://localhost:11434"
    assert custom_settings.text_game_host == "localhost"
    assert custom_settings.text_game_port == 9000
    assert custom_settings.log_level == "DEBUG"


def test_settings_environment_override(monkeypatch):
    """Test that environment variables override default values."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://env:pass@localhost:5432/env_db")
    monkeypatch.setenv("OPENAI_API_KEY", "env_key")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    
    settings = Settings()
    
    assert settings.database_url == "postgresql://env:pass@localhost:5432/env_db"
    assert settings.openai_api_key == "env_key"
    assert settings.log_level == "ERROR"