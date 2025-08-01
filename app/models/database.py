# app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text,text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.utils.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG  # Set to True to see SQL queries in console
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for database models
Base = declarative_base()

# Database Models
class NewsRecord(Base):
    __tablename__ = "news_records"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True, nullable=False)  # Stock symbol like TCS, INFY
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    headlines = Column(JSON, nullable=False)  # Store array of {title, sentiment} objects
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Database dependency for FastAPI
def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database utility functions
def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_cached_news(db, symbol: str, cache_minutes: int = 10):
    """Get cached news for a symbol if it exists within cache time"""
    from datetime import datetime, timedelta
    
    cache_time = datetime.utcnow() - timedelta(minutes=cache_minutes)
    
    cached_record = db.query(NewsRecord).filter(
        NewsRecord.symbol == symbol.upper(),
        NewsRecord.created_at > cache_time
    ).order_by(NewsRecord.created_at.desc()).first()
    
    return cached_record

def save_news_record(db, symbol: str, headlines: list):
    """Save news record to database"""
    try:
        news_record = NewsRecord(
            symbol=symbol.upper(),
            timestamp=datetime.utcnow(),
            headlines=headlines  # headlines is already array of {title, sentiment} objects
        )
        
        db.add(news_record)
        db.commit()
        db.refresh(news_record)
        
        print(f"✅ News record saved for {symbol}")
        return news_record
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving news record: {e}")
        raise e

# Initialize database when module is imported
if __name__ == "__main__":
    # Test database connection and create tables
    if check_database_connection():
        create_tables()
    else:
        print("Please check your database configuration in .env file")