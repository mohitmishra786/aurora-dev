"""
FastAPI REST API for AURORA-DEV.

Provides HTTP endpoints for managing projects, tasks,
agents, and workflow execution.

Example usage:
    uvicorn aurora_dev.interfaces.api.main:app --reload

Production features:
    - Rate limiting (token bucket)
    - Circuit breaker for resilience
    - JWT authentication (optional)
    - Dashboard data endpoints
"""
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aurora_dev.core.logging import get_logger
from aurora_dev.middleware.rate_limiter import RateLimiter, RateLimitConfig, RateLimitMiddleware
from aurora_dev.middleware.circuit_breaker import CircuitBreakerMiddleware, CircuitBreaker


logger = get_logger(__name__)


# Configuration from environment
ENABLE_RATE_LIMITING = os.getenv("AURORA_RATE_LIMITING", "true").lower() == "true"
ENABLE_CIRCUIT_BREAKER = os.getenv("AURORA_CIRCUIT_BREAKER", "true").lower() == "true"
RATE_LIMIT_RPM = int(os.getenv("AURORA_RATE_LIMIT_RPM", "60"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("AURORA-DEV API starting up...")
    logger.info(f"Rate limiting: {ENABLE_RATE_LIMITING}, Circuit breaker: {ENABLE_CIRCUIT_BREAKER}")
    yield
    logger.info("AURORA-DEV API shutting down...")


app = FastAPI(
    title="AURORA-DEV API",
    description="Multi-agent autonomous development system with production hardening",
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

# Rate limiting middleware
if ENABLE_RATE_LIMITING:
    rate_config = RateLimitConfig(
        requests_per_minute=RATE_LIMIT_RPM,
        burst_size=20,
        exempt_paths=["/health", "/docs", "/openapi.json", "/redoc"],
    )
    app.add_middleware(RateLimitMiddleware, limiter=RateLimiter(rate_config))

# Circuit breaker middleware
if ENABLE_CIRCUIT_BREAKER:
    circuit = CircuitBreaker(
        name="api_main",
    )
    app.add_middleware(CircuitBreakerMiddleware, circuit=circuit)


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
        "features": {
            "rate_limiting": ENABLE_RATE_LIMITING,
            "circuit_breaker": ENABLE_CIRCUIT_BREAKER,
        },
    }


# Import and include routers
from aurora_dev.interfaces.api.routes import projects, tasks, agents, workflows
from aurora_dev.interfaces.web.dashboard import router as dashboard_router

app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AURORA-DEV API",
        "version": "0.3.0",
        "docs": "/docs",
        "health": "/health",
    }
