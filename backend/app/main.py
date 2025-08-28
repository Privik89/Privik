from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .core.config import get_settings
from .api import api_router
from .database import create_tables

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered, zero-trust email security platform for real-time phishing protection",
    version="1.0.0",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Privik Email Security Platform")
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to Privik Email Security Platform",
        "description": "AI-powered, zero-trust email security for real-time phishing protection",
        "version": "1.0.0",
        "docs": "/docs"
    }


app.include_router(api_router, prefix="/api")


