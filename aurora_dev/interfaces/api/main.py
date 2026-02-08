"""
FastAPI REST API for AURORA-DEV.

Provides HTTP endpoints for managing projects, tasks,
agents, and workflow execution.

Example usage:
    uvicorn aurora_dev.interfaces.api.main:app --reload
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("AURORA-DEV API starting up...")
    yield
    logger.info("AURORA-DEV API shutting down...")


app = FastAPI(
    title="AURORA-DEV API",
    description="Multi-agent autonomous development system",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Check API health status."""
    return {
        "status": "healthy",
        "version": "0.3.0",
        "service": "aurora-dev-api",
    }


# Import and include routers
from aurora_dev.interfaces.api.routes import projects, tasks, agents, workflows

app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AURORA-DEV API",
        "version": "0.3.0",
        "docs": "/docs",
        "health": "/health",
    }
