# main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

from .database import engine, get_db
from .models import Base
from .security import (
    rate_limit_middleware,
    validation_middleware
)
from .auth import router as auth_router
from .routers import users_router, gift_cards_router, vendors_router
from .config import get_settings
from .logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "main.log")

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(validation_middleware)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(vendors_router)
app.include_router(gift_cards_router)

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Gift Card Wallet API"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint to verify database connectivity"""
    logger.info("Database health check initiated")
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database health check successful")
        return {"status": "Database connection successful"}
    except Exception as e:
        error_msg = f"Database health check failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"status": "Database connection failed", "error": str(e)}

@app.get("/db-schema")
async def db_schema():
    """Endpoint to retrieve the database schema"""
    logger.info("Database schema retrieval initiated")
    try:
        inspector = inspect(engine)
        schema = {}
        tables = inspector.get_table_names()
        logger.debug(f"Found {len(tables)} tables in database")
        
        for table_name in tables:
            logger.debug(f"Inspecting table: {table_name}")
            columns = inspector.get_columns(table_name)
            schema[table_name] = [
                {"name": column["name"], "type": str(column["type"])} 
                for column in columns
            ]
            logger.debug(f"Table {table_name}: {len(columns)} columns retrieved")
        
        logger.info("Database schema retrieved successfully")
        return schema
    except Exception as e:
        error_msg = f"Failed to retrieve database schema: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_msg = f"HTTP {exc.status_code} error occurred. Path: {request.url.path}, Detail: {exc.detail}"
    
    if exc.status_code >= 500:
        logger.error(error_msg)
    elif exc.status_code >= 400:
        logger.warning(error_msg)
    else:
        logger.info(error_msg)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_msg = f"Unhandled exception occurred. Path: {request.url.path}, Error: {str(exc)}"
    logger.error(error_msg, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )