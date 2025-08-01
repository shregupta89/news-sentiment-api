# app/models/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import settings

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
    symbol = Column(String(10), index=True, nullable=False, unique=True)  # Make symbol unique
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    headlines = Column(JSON, nullable=False)  # Store array of {title, sentiment} objects
    overall_sentiment = Column(String(20), nullable=True)  # majority vote: positive, negative, neutral
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
    """
    Get cached news for a symbol if it exists within cache time.
    Since symbol is now unique, we just check if it was updated recently.
    """
    from datetime import datetime, timedelta
    
    cache_time = datetime.utcnow() - timedelta(minutes=cache_minutes)
    
    # Find the record for this symbol
    cached_record = db.query(NewsRecord).filter(NewsRecord.symbol == symbol.upper()).first()
    
    # Check if it exists and was updated within cache time
    if cached_record and cached_record.updated_at > cache_time:
        print(f"  💾 Found cached data for {symbol} (updated {cache_minutes} minutes ago)")
        return cached_record
    elif cached_record:
        print(f"  ⏰ Cached data for {symbol} exists but is older than {cache_minutes} minutes")
        return None
    else:
        print(f"  🆕 No cached data found for {symbol}")
        return None

def save_news_record(db, symbol: str, headlines: list):
    """
    Save or update news record in database.
    If symbol exists, merge new headlines with existing ones (avoid duplicates).
    """
    try:
        symbol = symbol.upper()
        current_time = datetime.utcnow()
        
        # Check if record already exists
        existing_record = db.query(NewsRecord).filter(NewsRecord.symbol == symbol).first()
        
        if existing_record:
            # Merge headlines (avoid duplicates)
            existing_headlines = existing_record.headlines or []
            merged_headlines = merge_unique_headlines(existing_headlines, headlines)
            
            # Calculate overall sentiment
            overall_sentiment = calculate_overall_sentiment(merged_headlines)
            
            # Update existing record
            existing_record.headlines = merged_headlines
            existing_record.overall_sentiment = overall_sentiment  
            existing_record.timestamp = current_time
            existing_record.updated_at = current_time
            
            db.commit()
            db.refresh(existing_record)
            
            print(f"✅ Updated existing record for {symbol} with {len(headlines)} new headlines")
            return existing_record
        else:
            # Calculate overall sentiment for new record
            overall_sentiment = calculate_overall_sentiment(headlines)
            
            # Create new record
            news_record = NewsRecord(
                symbol=symbol,
                timestamp=current_time,
                headlines=headlines,
                overall_sentiment=overall_sentiment
            )
            
            db.add(news_record)
            db.commit()
            db.refresh(news_record)
            
            print(f"✅ Created new record for {symbol}")
            return news_record
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error saving news record: {e}")
        raise e

def merge_unique_headlines(existing_headlines: list, new_headlines: list) -> list:
    """
    Merge new headlines with existing ones, avoiding duplicates based on title similarity
    """
    if not existing_headlines:
        return new_headlines
    
    # Extract existing titles for comparison
    existing_titles = set()
    for headline in existing_headlines:
        if isinstance(headline, dict) and 'title' in headline:
            # Normalize title for comparison (lowercase, remove extra spaces)
            normalized_title = ' '.join(headline['title'].lower().split())
            existing_titles.add(normalized_title)
    
    # Add only new unique headlines
    merged = existing_headlines.copy()
    added_count = 0
    
    for new_headline in new_headlines:
        if isinstance(new_headline, dict) and 'title' in new_headline:
            normalized_new_title = ' '.join(new_headline['title'].lower().split())
            
            # Check if this headline is already present
            if normalized_new_title not in existing_titles:
                merged.append(new_headline)
                existing_titles.add(normalized_new_title)
                added_count += 1
    
    print(f"  📝 Added {added_count} unique headlines (filtered {len(new_headlines) - added_count} duplicates)")
    return merged

def calculate_overall_sentiment(headlines: list) -> str:
    """
    Calculate overall sentiment based on majority vote of all headlines
    """
    if not headlines:
        return "neutral"
    
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for headline in headlines:
        if isinstance(headline, dict) and 'sentiment' in headline:
            sentiment = headline['sentiment'].lower()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
    
    # Find majority sentiment
    if sentiment_counts["positive"] > sentiment_counts["negative"] and sentiment_counts["positive"] > sentiment_counts["neutral"]:
        return "positive"
    elif sentiment_counts["negative"] > sentiment_counts["positive"] and sentiment_counts["negative"] > sentiment_counts["neutral"]:
        return "negative"
    else:
        return "neutral"

# Initialize database when module is imported
if __name__ == "__main__":
    # Test database connection and create tables
    if check_database_connection():
        create_tables()
    else:
        print("Please check your database configuration in .env file")