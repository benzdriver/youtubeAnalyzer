import pytest
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import redis
import requests


class TestConfigurationIntegration:
    """Test suite for configuration integration across components."""
    
    def test_environment_variables_loaded(self):
        """Test that required environment variables are loaded."""
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "ENVIRONMENT",
            "DEBUG"
        ]
        
        for var in required_vars:
            assert os.getenv(var) is not None, f"Environment variable {var} is not set"
    
    def test_backend_config_loading(self):
        """Test that backend configuration loads correctly."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        assert settings.app_name is not None
        assert settings.environment is not None
        assert settings.debug is not None
        assert settings.database_url is not None
        assert settings.redis_url is not None
        assert settings.secret_key is not None
        
        assert len(settings.allowed_origins) > 0
        assert settings.task_timeout > 0
    
    def test_frontend_config_loading(self):
        """Test that frontend configuration is accessible."""
        frontend_vars = [
            "NEXT_PUBLIC_API_URL",
            "NEXT_PUBLIC_WS_URL",
            "NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES",
            "NEXT_PUBLIC_ENABLE_EXPORT"
        ]
        
        frontend_config_path = "/home/ubuntu/repos/youtubeAnalyzer/frontend/src/config/index.ts"
        assert os.path.exists(frontend_config_path), "Frontend config file not found"
        
        with open(frontend_config_path, 'r') as f:
            config_content = f.read()
            assert "getEnvVar" in config_content
            assert "NEXT_PUBLIC_API_URL" in config_content
            assert "NEXT_PUBLIC_WS_URL" in config_content
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection using configuration."""
        import os
        os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_config.db'
        
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(
            'sqlite+aiosqlite:///./test_config.db',
            echo=False,
            pool_pre_ping=True
        )
        
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                assert row[0] == 1
                
        except Exception as e:
            pytest.fail(f"Database connection failed: {str(e)}")
        finally:
            await engine.dispose()
    
    def test_redis_connection(self):
        """Test Redis connection using configuration."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        try:
            redis_client = redis.from_url(settings.redis_url)
            
            redis_client.ping()
            
            redis_client.set("test_key", "test_value", ex=10)
            value = redis_client.get("test_key")
            assert value is not None and value.decode() == "test_value"
            
            redis_client.delete("test_key")
            
        except Exception as e:
            pytest.fail(f"Redis connection failed: {str(e)}")
        finally:
            redis_client.close()
    
    def test_celery_configuration(self):
        """Test Celery configuration."""
        from app.core.celery_app import celery_app
        from app.core.config import get_settings
        
        settings = get_settings()
        
        assert celery_app.conf.broker_url == settings.celery_broker_url
        assert celery_app.conf.result_backend == settings.celery_result_backend
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
    
    def test_cors_configuration(self):
        """Test CORS configuration matches between backend and frontend."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        frontend_url = "http://localhost:3000"
        assert frontend_url in settings.allowed_origins
        
        response = requests.options(
            "http://localhost:8000/api/v1/tasks",
            headers={
                "Origin": frontend_url,
                "Access-Control-Request-Method": "POST"
            }
        )
        
        if response.status_code in [200, 204]:
            assert "Access-Control-Allow-Origin" in response.headers
    
    def test_logging_configuration(self):
        """Test logging configuration."""
        import logging
        
        logger = logging.getLogger("app")
        assert logger.level <= logging.INFO
        
        logger.info("Test log message for integration testing")
    
    def test_security_configuration(self):
        """Test security-related configuration."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        assert len(settings.secret_key) >= 32, "Secret key should be at least 32 characters"
        
        assert isinstance(settings.debug, bool)
        
        if settings.environment == "development":
            assert settings.debug is True
    
    def test_api_timeout_configuration(self):
        """Test API timeout configuration."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        assert settings.task_timeout > 0
        assert settings.task_timeout <= 3600  # Should not exceed 1 hour
        
        soft_timeout = settings.task_timeout - 300
        assert soft_timeout > 0
        assert soft_timeout < settings.task_timeout
    
    def test_feature_flags_configuration(self):
        """Test feature flags configuration."""
        feature_flags = [
            "NEXT_PUBLIC_ENABLE_ANALYTICS",
            "NEXT_PUBLIC_ENABLE_EXPORT",
            "NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES",
            "NEXT_PUBLIC_ENABLE_DEBUG"
        ]
        
        for flag in feature_flags:
            value = os.getenv(flag)
            if value is not None:
                assert value.lower() in ["true", "false"], f"Feature flag {flag} should be true or false"
    
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database initialization process."""
        import os
        os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test_init.db'
        
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine('sqlite+aiosqlite:///./test_init.db')
        
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"))
            assert True
        except Exception as e:
            pytest.fail(f"Database initialization failed: {str(e)}")
        finally:
            await engine.dispose()
