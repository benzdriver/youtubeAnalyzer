import pytest
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../backend"))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("DATABASE_URL", "postgresql://test_user:test_password@localhost:5432/youtube_analyzer_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("SECRET_KEY", "test_secret_key_for_integration_testing_32_chars_minimum")
    os.environ.setdefault("OPENAI_API_KEY", "test_key_for_integration_testing")
    os.environ.setdefault("YOUTUBE_API_KEY", "test_key_for_integration_testing")
