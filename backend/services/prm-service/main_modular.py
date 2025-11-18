"""
PRM Service - Patient Relationship Management (Modular)
Journey orchestration, communications, and patient engagement

This is the new modular entry point for the PRM service.
The monolithic main.py can be deprecated once migration is complete.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.database.connection import engine
from shared.database.models import Base

from core.redis_client import redis_manager
from core.config import settings
from api.router import api_router


# Initialize FastAPI app
app = FastAPI(
    title="PRM Service",
    description="Patient Relationship Management - Journey orchestration and communications",
    version="0.2.0",  # Incremented version for modular release
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prm-service",
        "version": "0.2.0",
        "architecture": "modular",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Include Routers ====================

# Include the main API router with all module endpoints
app.include_router(api_router)


# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("PRM Service (Modular) starting up...")

    try:
        # Initialize database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")

        # Connect to Redis
        if settings.REDIS_URL:
            await redis_manager.connect()
            logger.info("Redis connected")

        logger.info("PRM Service (Modular) ready!")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("PRM Service shutting down...")

    try:
        # Close Redis connection
        await redis_manager.close()
        logger.info("Redis connection closed")

        logger.info("PRM Service shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007, reload=True)
