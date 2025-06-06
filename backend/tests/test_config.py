"""
Configuration Tests

This module contains unit tests for the configuration management system,
including environment variable loading, validation, and error handling.
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestConfigurationLoading:
    """Test configuration loading and validation."""
    
    def test_config_loading_with_valid_env(self):
        """Test configuration loading with valid environment variables."""
        test_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'REDIS_URL': 'redis://localhost:6379',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            settings = Settings()
            
            assert settings.app_name == "YouTube Analyzer"
            assert settings.database_url == test_env['DATABASE_URL']
            assert settings.redis_url == test_env['REDIS_URL']
            assert settings.openai_api_key == test_env['OPENAI_API_KEY']
            assert settings.youtube_api_key == test_env['YOUTUBE_API_KEY']
            assert settings.secret_key == test_env['SECRET_KEY']
            assert settings.environment == "development"
            assert settings.debug is False
    
    def test_config_loading_with_defaults(self):
        """Test configuration loading with default values."""
        minimal_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()
            
            assert settings.app_name == "YouTube Analyzer"
            assert settings.redis_url == "redis://localhost:6379"
            assert settings.allowed_origins == ["http://localhost:3000"]
            assert settings.environment == "development"
            assert settings.debug is False
    
    def test_config_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2


class TestEnvironmentVariableValidation:
    """Test environment variable validation and error handling."""
    
    def test_missing_database_url_raises_error(self):
        """Test that missing DATABASE_URL raises ValidationError."""
        incomplete_env = {
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "database_url" in str(exc_info.value).lower()
    
    def test_missing_openai_api_key_raises_error(self):
        """Test that missing OPENAI_API_KEY raises ValidationError."""
        incomplete_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "openai_api_key" in str(exc_info.value).lower()
    
    def test_missing_youtube_api_key_raises_error(self):
        """Test that missing YOUTUBE_API_KEY raises ValidationError."""
        incomplete_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "youtube_api_key" in str(exc_info.value).lower()
    
    def test_missing_secret_key_raises_error(self):
        """Test that missing SECRET_KEY raises ValidationError."""
        incomplete_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key'
        }
        
        with patch.dict(os.environ, incomplete_env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "secret_key" in str(exc_info.value).lower()
    
    def test_empty_database_url_raises_error(self):
        """Test that empty DATABASE_URL raises ValidationError."""
        invalid_env = {
            'DATABASE_URL': '',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, invalid_env, clear=True):
            with pytest.raises(ValidationError):
                Settings()


class TestConfigurationValidation:
    """Test configuration validation functions."""
    
    def test_valid_environment_values(self):
        """Test that valid environment values are accepted."""
        for env_value in ["development", "production", "test"]:
            test_env = {
                'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
                'OPENAI_API_KEY': 'test-openai-key',
                'YOUTUBE_API_KEY': 'test-youtube-key',
                'SECRET_KEY': 'test-secret-key-minimum-32-characters-long',
                'ENVIRONMENT': env_value
            }
            
            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                assert settings.environment == env_value
    
    def test_debug_mode_configuration(self):
        """Test debug mode configuration."""
        test_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long',
            'DEBUG': 'true'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.debug is True
        
        test_env['DEBUG'] = 'false'
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.debug is False
    
    def test_allowed_origins_configuration(self):
        """Test CORS allowed origins configuration."""
        test_env = {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key',
            'SECRET_KEY': 'test-secret-key-minimum-32-characters-long',
            'ALLOWED_ORIGINS': 'http://localhost:3000,https://example.com,https://app.example.com'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            expected_origins = [
                'http://localhost:3000',
                'https://example.com',
                'https://app.example.com'
            ]
            assert settings.allowed_origins == expected_origins


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_case_insensitive_environment_variables(self):
        """Test that environment variables are case insensitive."""
        test_env = {
            'database_url': 'postgresql://test:test@localhost:5432/test_db',
            'openai_api_key': 'test-openai-key',
            'youtube_api_key': 'test-youtube-key',
            'secret_key': 'test-secret-key-minimum-32-characters-long'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.database_url == test_env['database_url']
    
    def test_whitespace_handling(self):
        """Test that whitespace in environment variables is handled correctly."""
        test_env = {
            'DATABASE_URL': '  postgresql://test:test@localhost:5432/test_db  ',
            'OPENAI_API_KEY': '  test-openai-key  ',
            'YOUTUBE_API_KEY': '  test-youtube-key  ',
            'SECRET_KEY': '  test-secret-key-minimum-32-characters-long  '
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.database_url.strip() == test_env['DATABASE_URL'].strip()
    
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        for true_value in ['true', 'True', 'TRUE', '1', 'yes', 'Yes']:
            test_env = {
                'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
                'OPENAI_API_KEY': 'test-openai-key',
                'YOUTUBE_API_KEY': 'test-youtube-key',
                'SECRET_KEY': 'test-secret-key-minimum-32-characters-long',
                'DEBUG': true_value
            }
            
            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                assert settings.debug is True
        
        for false_value in ['false', 'False', 'FALSE', '0', 'no', 'No', '']:
            test_env = {
                'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
                'OPENAI_API_KEY': 'test-openai-key',
                'YOUTUBE_API_KEY': 'test-youtube-key',
                'SECRET_KEY': 'test-secret-key-minimum-32-characters-long',
                'DEBUG': false_value
            }
            
            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                assert settings.debug is False


if __name__ == "__main__":
    pytest.main([__file__])
