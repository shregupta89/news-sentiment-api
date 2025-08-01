# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, get_cached_news, save_news_record, uct_now
from models.schemas import NewsRequest, NewsResponse, HeadlineWithSentiment
from services.news_service import NewsService, MockNewsService
from services.sentiment_service import SentimentService, MockSentimentService
from utils.config import settings

# Create router
router = APIRouter()

# Initialize services (with fallback to mock services)
try:
    if settings.RAPIDAPI_KEY and settings.OPENAI_API_KEY:
        news_service = NewsService()
        sentiment_service = SentimentService()
        print("✅ Using live API services")
    else:
        news_service = MockNewsService()
        sentiment_service = MockSentimentService()
        print("🧪 Using mock services (add API keys to use live services)")
except Exception as e:
    print(f"⚠️ Error initializing services, falling back to mock: {e}")
    news_service = MockNewsService()
    sentiment_service = MockSentimentService()

@router.post("/news-sentiment", response_model=NewsResponse)
async def get_news_sentiment(
    request: NewsRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch news headlines for a stock symbol and analyze sentiment.
    
    - **symbol**: Indian stock symbol (e.g., TCS, INFY, RELIANCE)
    - Returns headlines with sentiment analysis
    - Uses 10-minute cache to avoid duplicate API calls
    """
    
    try:
        # Step 1: Check cache first (10-minute rule)
        print(f"🔍 Checking cache for symbol: {request.symbol}")
        cached_news = get_cached_news(db, request.symbol, settings.CACHE_EXPIRY_MINUTES)
        
        if cached_news:
            print(f"✅ Found cached data for {request.symbol}")
            # Convert database headlines to response format (latest 3 only)
            latest_headlines = cached_news.headlines[-3:] if len(cached_news.headlines) >= 3 else cached_news.headlines
            headlines = [
                HeadlineWithSentiment(
                    title=headline["title"],
                    sentiment=headline["sentiment"]
                )
                for headline in latest_headlines
            ]
            
            return NewsResponse(
                symbol=cached_news.symbol,
                timestamp=cached_news.timestamp,
                headlines=headlines,
                overall_sentiment=cached_news.overall_sentiment or "neutral"
            )
        
        # Step 2: Fetch fresh news (cache miss)
        print(f"📰 Fetching fresh news for {request.symbol}")
        news_articles = await news_service.fetch_news(request.symbol)
        
        if not news_articles:
            raise HTTPException(
                status_code=404, 
                detail=f"No recent news found for symbol: {request.symbol}"
            )
        
        # Limit to latest 3 news articles
        latest_articles = news_articles[-3:] if len(news_articles) >= 3 else news_articles
        
        # Step 3: Analyze sentiment for each headline
        print(f"🤖 Analyzing sentiment for {len(latest_articles)} headlines")
        headlines_with_sentiment = []
        
        for article in latest_articles:
            try:
                sentiment = await sentiment_service.analyze_sentiment(article.title)
                headlines_with_sentiment.append({
                    "title": article.title,
                    "sentiment": sentiment
                })
                print(f"  ✓ '{article.title[:50]}...' → {sentiment}")
            except Exception as e:
                print(f"  ✗ Error analyzing sentiment for '{article.title}': {e}")
                # Default to neutral if sentiment analysis fails
                headlines_with_sentiment.append({
                    "title": article.title,
                    "sentiment": "neutral"
                })
        
        # Step 4: Save to database
        print(f"💾 Saving results to database")
        timestamp = uct_now()  # Use timezone-aware ist datetime
        news_record = save_news_record(db, request.symbol, headlines_with_sentiment)
        
        # Step 5: Format response
        response_headlines = [
            HeadlineWithSentiment(
                title=headline["title"],
                sentiment=headline["sentiment"]
            )
            for headline in headlines_with_sentiment
        ]
        
        print(f"🎉 Successfully processed {request.symbol}")
        return NewsResponse(
            symbol=request.symbol,
            timestamp=timestamp,
            headlines=response_headlines,
            overall_sentiment=news_record.overall_sentiment or "neutral"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Unexpected error processing {request.symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing {request.symbol}: {str(e)}"
        )

@router.get("/news-sentiment/{symbol}")
async def get_cached_news_sentiment(symbol: str, db: Session = Depends(get_db)):
    """
    Get the most recent cached news sentiment for a symbol (if exists).
    This is a GET endpoint for convenience.
    """
    try:
        cached_news = get_cached_news(db, symbol, cache_minutes=60)  # Check last hour
        
        if not cached_news:
            raise HTTPException(
                status_code=404,
                detail=f"No cached data found for symbol: {symbol}"
            )
        
        # Get latest 3 headlines only
        latest_headlines = cached_news.headlines[-3:] if len(cached_news.headlines) >= 3 else cached_news.headlines
        headlines = [
            HeadlineWithSentiment(
                title=headline["title"],
                sentiment=headline["sentiment"]
            )
            for headline in latest_headlines
        ]
        
        return NewsResponse(
            symbol=cached_news.symbol,
            timestamp=cached_news.timestamp,
            headlines=headlines,
            overall_sentiment=cached_news.overall_sentiment or "neutral"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cached data: {str(e)}"
        )