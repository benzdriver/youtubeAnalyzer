import logging
import time

from fastapi import Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_TASKS = Gauge("active_analysis_tasks", "Number of active analysis tasks")

TASK_COMPLETION_TIME = Histogram(
    "task_completion_seconds", "Task completion time in seconds", ["task_type"]
)

CELERY_TASK_COUNT = Counter(
    "celery_tasks_total", "Total Celery tasks", ["task_name", "status"]
)

DATABASE_CONNECTIONS = Gauge(
    "database_connections_active", "Number of active database connections"
)

REDIS_CONNECTIONS = Gauge(
    "redis_connections_active", "Number of active Redis connections"
)

MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        method = request.method
        path = request.url.path

        normalized_path = self._normalize_path(path)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"Request failed: {e}")
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            REQUEST_COUNT.labels(
                method=method, endpoint=normalized_path, status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(method=method, endpoint=normalized_path).observe(
                duration
            )

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders"""
        import re

        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
        )
        path = re.sub(r"/\d+", "/{id}", path)

        return path


def record_task_start(task_type: str):
    """Record when a task starts"""
    ACTIVE_TASKS.inc()
    CELERY_TASK_COUNT.labels(task_name=task_type, status="started").inc()


def record_task_completion(task_type: str, duration: float, success: bool = True):
    """Record when a task completes"""
    ACTIVE_TASKS.dec()
    TASK_COMPLETION_TIME.labels(task_type=task_type).observe(duration)

    status = "completed" if success else "failed"
    CELERY_TASK_COUNT.labels(task_name=task_type, status=status).inc()


def update_system_metrics():
    """Update system-level metrics"""
    import psutil

    memory = psutil.virtual_memory()
    MEMORY_USAGE.set(memory.used)


def get_metrics() -> str:
    """Return Prometheus format metrics"""
    try:
        update_system_metrics()
        return generate_latest()
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return ""


def get_metrics_content_type() -> str:
    """Return the content type for metrics"""
    return CONTENT_TYPE_LATEST
