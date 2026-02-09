"""FastAPI application entry point."""

# CRITICAL: Disable MCP filesystem BEFORE any imports that use agents
# This must happen before importing chat_service, which imports agents
import os
import warnings

os.environ['MCP_DISABLE_FILESYSTEM'] = '1'
os.environ['MCP_NO_SERVER'] = '1'
warnings.filterwarnings('ignore', message='.*Unable to add filesystem.*')

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .core.database import create_db_and_tables
from .api.health import router as health_router
from .api.tasks import router as tasks_router
from .api.chat import router as chat_router
from .api.mcp import router as mcp_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info("Starting application...")
    try:
        create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue without database for health checks
    yield
    # Shutdown
    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Todo Application API",
        description="Multi-user Todo application with JWT authentication",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js dev server
            "http://127.0.0.1:3000",
            # Vercel Production
            "https://my-todo-app-jet-pi.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    app.include_router(mcp_router, prefix="/api/mcp", tags=["mcp"])

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Todo Application API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
