"""
YouTube Analyzer Backend - Main FastAPI Application

This module contains the main FastAPI application instance and configuration.
It sets up the API routes, middleware, and application lifecycle events.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.api.v1.websocket import websocket_manager
from app.core.config import get_settings
from app.core.database import init_db
from app.utils.exceptions import YouTubeAnalyzerError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    settings = get_settings()
    
    print(f"Starting {settings.app_name} in {settings.environment} mode")
    await init_db()
    logging.info("Application started")
    
    yield
    
    print(f"Shutting down {settings.app_name}")
    logging.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered YouTube video analysis platform",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logging.info(
            "Request processed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    @app.exception_handler(YouTubeAnalyzerError)
    async def youtube_analyzer_exception_handler(
        request: Request, exc: YouTubeAnalyzerError
    ):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {"code": exc.__class__.__name__, "message": str(exc)},
                "timestamp": time.time(),
                "request_id": str(uuid.uuid4()),
            },
        )

    app.include_router(api_router, prefix="/api/v1")

    @app.websocket("/ws/{task_id}")
    async def websocket_endpoint(websocket: WebSocket, task_id: str):
        await websocket_manager.connect(websocket, task_id)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.disconnect(task_id)

    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring and load balancers."""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": settings.app_name,
                "environment": settings.environment,
                "version": "1.0.0",
                "timestamp": time.time()
            }
        )
    
    @app.get("/")
    async def root():
        """Root endpoint with basic API information."""
        return JSONResponse(
            content={
                "message": f"Welcome to {settings.app_name}",
                "version": "1.0.0",
                "docs": "/docs" if settings.debug else "Documentation disabled in production",
                "health": "/health"
            }
        )
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
