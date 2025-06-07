import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


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

    database_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/youtube_analyzer"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 10

    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    openai_project: Optional[str] = None
    youtube_api_key: Optional[str] = None

    secret_key: str = "your-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    celery_broker_url: str = "redis://localhost:6379"
    celery_result_backend: str = "redis://localhost:6379"
    celery_worker_concurrency: int = 4

    whisper_model_size: str = "base"
    max_audio_duration: int = 3600  # 1 hour in seconds
    whisper_device: str = "auto"  # auto, cpu, cuda

    max_comments: int = 1000
    default_analysis_depth: str = "detailed"
    max_concurrent_tasks: int = 5
    task_timeout: int = 3600

    upload_dir: str = "/tmp/uploads"
    storage_path: str = "./storage"
    max_file_size: int = 2 * 1024 * 1024 * 1024

    youtube_max_comments: int = 1000
    youtube_audio_quality: str = "192K"
    youtube_audio_format: str = "wav"
    audio_cleanup_after_hours: int = 24

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = False
    log_file_path: str = "logs/app.log"
    log_sql_queries: bool = False
    log_http_requests: bool = False
    log_container_info: bool = True
    log_json_format: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


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
    settings = Settings()
    validate_youtube_config(settings)
    return settings


def validate_youtube_config(settings: Settings) -> None:
    """Validate YouTube-specific configuration.

    Args:
        settings: The settings instance to validate

    Raises:
        MissingEnvironmentVariable: If YouTube API key is missing when needed
        InvalidConfigurationValue: If configuration values are invalid
    """

    if not settings.storage_path:
        raise InvalidConfigurationValue("Storage path cannot be empty")

    if not settings.upload_dir:
        raise InvalidConfigurationValue("Upload directory cannot be empty")

    if settings.youtube_max_comments <= 0:
        raise InvalidConfigurationValue("YouTube max comments must be positive")

    if settings.audio_cleanup_after_hours < 0:
        raise InvalidConfigurationValue("Audio cleanup hours cannot be negative")

    if settings.whisper_model_size not in [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
        "large-v2",
        "large-v3",
    ]:
        raise InvalidConfigurationValue(
            f"Invalid Whisper model size: {settings.whisper_model_size}"
        )

    if settings.whisper_device not in ["auto", "cpu", "cuda"]:
        raise InvalidConfigurationValue(
            f"Invalid Whisper device: {settings.whisper_device}"
        )

    if settings.max_audio_duration <= 0:
        raise InvalidConfigurationValue("Max audio duration must be positive")


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
