from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class ConfigurationError(Exception):
    """Configuration related errors."""
    pass


class MissingEnvironmentVariable(ConfigurationError):
    """Missing required environment variable."""
    pass


class InvalidConfigurationValue(ConfigurationError):
    """Invalid configuration value."""
    pass


class Settings(BaseSettings):
    """Application configuration settings.
    
    This class manages all configuration settings for the YouTube Analyzer application.
    It uses Pydantic BaseSettings to automatically load values from environment variables
    and provides validation for required settings.
    """
    
    app_name: str = "YouTube Analyzer"
    debug: bool = False
    environment: str = "development"
    version: str = "1.0.0"
    
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 10
    
    openai_api_key: str
    openai_organization: Optional[str] = None
    openai_project: Optional[str] = None
    youtube_api_key: str
    
    secret_key: str
    allowed_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_worker_concurrency: int = 4
    
    whisper_model_size: str = "base"
    max_audio_duration: int = 3600  # 1 hour in seconds
    
    max_comments: int = 1000
    default_analysis_depth: str = "detailed"
    
    upload_dir: str = "/tmp/uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def validate_config(settings_instance: Settings) -> None:
    """Validate configuration completeness and correctness.
    
    Args:
        settings_instance: The settings instance to validate
        
    Raises:
        MissingEnvironmentVariable: If required environment variables are missing
        InvalidConfigurationValue: If configuration values are invalid
    """
    required_vars = [
        ('database_url', 'DATABASE_URL'),
        ('openai_api_key', 'OPENAI_API_KEY'),
        ('youtube_api_key', 'YOUTUBE_API_KEY'),
        ('secret_key', 'SECRET_KEY')
    ]
    
    missing_vars = []
    for attr_name, env_name in required_vars:
        value = getattr(settings_instance, attr_name, None)
        if not value or (isinstance(value, str) and not value.strip()):
            missing_vars.append(env_name)
    
    if missing_vars:
        raise MissingEnvironmentVariable(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    if settings_instance.environment not in ["development", "production", "test"]:
        raise InvalidConfigurationValue(
            f"Invalid environment: {settings_instance.environment}. "
            "Must be one of: development, production, test"
        )
    
    if settings_instance.whisper_model_size not in ["tiny", "base", "small", "medium", "large"]:
        raise InvalidConfigurationValue(
            f"Invalid whisper_model_size: {settings_instance.whisper_model_size}. "
            "Must be one of: tiny, base, small, medium, large"
        )
    
    if settings_instance.default_analysis_depth not in ["basic", "detailed", "comprehensive"]:
        raise InvalidConfigurationValue(
            f"Invalid default_analysis_depth: {settings_instance.default_analysis_depth}. "
            "Must be one of: basic, detailed, comprehensive"
        )
    
    if not settings_instance.database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise InvalidConfigurationValue(
            "database_url must be a PostgreSQL connection string"
        )
    
    if not settings_instance.redis_url.startswith("redis://"):
        raise InvalidConfigurationValue(
            "redis_url must be a Redis connection string"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function creates and caches a Settings instance, ensuring that
    configuration is loaded only once and validated.
    
    Returns:
        Settings: The validated settings instance
        
    Raises:
        ConfigurationError: If configuration validation fails
    """
    try:
        settings_instance = Settings()
        validate_config(settings_instance)
        return settings_instance
    except Exception as e:
        if isinstance(e, (MissingEnvironmentVariable, InvalidConfigurationValue)):
            raise
        raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e


settings = get_settings()


def reload_settings() -> Settings:
    """Reload settings by clearing the cache.
    
    This is useful for testing or when configuration needs to be reloaded
    at runtime.
    
    Returns:
        Settings: The new settings instance
    """
    get_settings.cache_clear()
    return get_settings()


def is_development() -> bool:
    """Check if running in development environment.
    
    Returns:
        bool: True if in development mode
    """
    return settings.environment == "development"


def is_production() -> bool:
    """Check if running in production environment.
    
    Returns:
        bool: True if in production mode
    """
    return settings.environment == "production"


def is_testing() -> bool:
    """Check if running in test environment.
    
    Returns:
        bool: True if in test mode
    """
    return settings.environment == "test"
