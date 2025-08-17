"""
Basic tests to verify testing setup works.
"""

import pytest


def test_basic_import():
    """Test that we can import the config module."""
    import sys
    import os
    
    # Add the ai-agent service to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))
    
    try:
        from core.config import Settings
        assert Settings is not None
        print("✅ Config import successful")
    except ImportError as e:
        pytest.fail(f"Failed to import config: {e}")


def test_settings_creation():
    """Test that we can create a Settings instance."""
    import sys
    import os
    
    # Add the ai-agent service to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))
    
    from core.config import Settings
    
    settings = Settings()
    assert settings.database_url == "postgresql://aivta_user:aivta_password@database:5432/aivta"
    assert settings.log_level == "INFO"
    print("✅ Settings creation successful")


def test_environment_override():
    """Test that environment variables override defaults."""
    import sys
    import os
    
    # Add the ai-agent service to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'ai-agent'))
    
    from core.config import Settings
    
    # Set environment variable
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    settings = Settings()
    assert settings.log_level == "DEBUG"
    
    # Clean up
    del os.environ["LOG_LEVEL"]
    print("✅ Environment override successful")


if __name__ == "__main__":
    # Run tests manually
    test_basic_import()
    test_settings_creation()
    test_environment_override()
    print("All basic tests passed!")