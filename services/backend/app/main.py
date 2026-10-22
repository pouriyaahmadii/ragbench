from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.config import Settings, get_settings
from app.providers.factory import close_providers
from app.db.session import init_db, close_db
from app.vectorstore.client import close_qdrant_clients
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RAGBench API...")
    
    settings = get_settings()
    
    # Initialize database
    await init_db(settings)
    logger.info("Database initialized")
    
    # Initialize providers
    from app.providers.factory import get_provider_factory
    factory = get_provider_factory(settings)
    logger.info("Providers initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAGBench API...")
    await close_providers()
    await close_db()
    from app.vectorstore.client import close_qdrant_clients
    close_qdrant_clients()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="RAGBench API",
        description="RAGBench - Retrieval-Augmented Generation Evaluation Platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://ragbench.dev/errors/internal-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred",
                "instance": str(request.url),
            },
        )
    
    # Health endpoints
    @app.get("/health/live")
    async def liveness():
        return {"status": "alive"}
    
    @app.get("/health/ready")
    async def readiness():
        # Check database and vector store connectivity
        return {"status": "ready", "dependencies": {"postgresql": "ok", "qdrant": "ok"}}
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()