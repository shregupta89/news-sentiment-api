# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

# Import our modules
from models.database import get_db, create_tables, check_database_connection
from models.schemas import NewsRequest, NewsResponse
from api.routes import router as news_router
from utils.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for fetching news and analyzing sentiment for Indian stock symbols",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI
)

# Add CORS middleware (for frontend integration later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router, prefix="/api/v1")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "News Sentiment API is running!",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that also verifies database connection"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    print("🚀 Starting News Sentiment API...")
    
    # Check database connection
    if check_database_connection():
        # Create tables if they don't exist
        create_tables()
        print("✅ Database initialized successfully")
    else:
        print("❌ Database connection failed!")
        
    print(f"📝 API Documentation available at: http://localhost:8000/docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down News Sentiment API...")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "message": "Check /docs for available endpoints"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "message": "Something went wrong on our end"}

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )


#     Main FastAPI App:

# ✅ Health check endpoints
# ✅ Database initialization on startup
# ✅ CORS middleware for frontend integration
# ✅ Error handling
# ✅ Auto-generated API docs at /docs