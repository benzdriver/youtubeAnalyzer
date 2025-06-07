import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from .config import get_settings


class ContainerAwareFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes container-specific information."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["service"] = os.environ.get("SERVICE_NAME", "backend")
        log_record["container_id"] = os.environ.get("HOSTNAME", "unknown")
        log_record["environment"] = os.environ.get("ENVIRONMENT", "development")

        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


class ContainerLogFilter(logging.Filter):
    """Filter to add container-specific context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.container_id = os.environ.get("HOSTNAME", "unknown")
        record.service_name = os.environ.get("SERVICE_NAME", "backend")
        record.pod_name = os.environ.get("POD_NAME", "unknown")
        return True


def setup_logging() -> None:
    """Configure application logging with container-aware settings."""
    settings = get_settings()

    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    if settings.log_json_format:
        formatter = ContainerAwareFormatter(
            "%(timestamp)s %(service)s %(container_id)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s"
        )
    else:
        formatter = logging.Formatter(settings.log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContainerLogFilter())
    root_logger.addHandler(console_handler)

    if settings.enable_file_logging:
        os.makedirs(os.path.dirname(settings.log_file_path), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContainerLogFilter())
        root_logger.addHandler(file_handler)

    if settings.log_container_info:
        logger = logging.getLogger(__name__)
        logger.info(
            "Container logging initialized",
            extra={
                "container_id": os.environ.get("HOSTNAME", "unknown"),
                "service_name": os.environ.get("SERVICE_NAME", "backend"),
                "log_level": settings.log_level,
                "json_format": settings.log_json_format,
                "file_logging": settings.enable_file_logging,
            },
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with container-aware configuration."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra fields to log records."""

    def __init__(self, logger: logging.Logger, **extra_fields):
        self.logger = logger
        self.extra_fields = extra_fields
        self.old_factory = None

    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_fields = self.extra_fields
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_container_health(
    service_name: str, status: str, details: Optional[Dict[str, Any]] = None
) -> None:
    """Log container health status with structured data."""
    logger = get_logger("container.health")

    health_data = {
        "service": service_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "container_id": os.environ.get("HOSTNAME", "unknown"),
    }

    if details:
        health_data.update(details)

    if status == "healthy":
        logger.info("Container health check passed", extra=health_data)
    elif status == "unhealthy":
        logger.error("Container health check failed", extra=health_data)
    else:
        logger.warning("Container health check status unknown", extra=health_data)


def log_startup_info() -> None:
    """Log container startup information."""
    logger = get_logger("container.startup")

    startup_info = {
        "container_id": os.environ.get("HOSTNAME", "unknown"),
        "service_name": os.environ.get("SERVICE_NAME", "backend"),
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": sys.version,
        "startup_time": datetime.utcnow().isoformat(),
    }

    logger.info("Container startup completed", extra=startup_info)


def log_database_connection(
    status: str, database_url: str, error: Optional[str] = None
) -> None:
    """Log database connection status."""
    logger = get_logger("database.connection")

    connection_data = {
        "status": status,
        "database_url": (
            database_url.split("@")[-1] if "@" in database_url else database_url
        ),  # Hide credentials
        "timestamp": datetime.utcnow().isoformat(),
    }

    if error:
        connection_data["error"] = error
        logger.error("Database connection failed", extra=connection_data)
    else:
        logger.info("Database connection established", extra=connection_data)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None,
) -> None:
    """Log API request with timing information."""
    settings = get_settings()

    if not settings.log_http_requests:
        return

    logger = get_logger("api.requests")

    request_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if user_id:
        request_data["user_id"] = user_id

    if status_code >= 400:
        logger.warning("API request completed with error", extra=request_data)
    else:
        logger.info("API request completed", extra=request_data)
