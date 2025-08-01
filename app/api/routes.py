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
from services.validation_service import stock_validator  # ← NEW IMPORT
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
        # ====== NEW VALIDATION STEP ======
        # Step 0: Validate stock symbol before processing
        print(f"🔍 Validating stock symbol: {request.symbol}")
        
        if not stock_validator.is_valid_symbol(request.symbol):
            # Get stock info for better error message
            stock_info = stock_validator.get_stock_info(request.symbol)
            suggestions = stock_validator.get_suggestions(request.symbol, limit=3)
            
            error_detail = {
                "error": "Invalid stock symbol",
                "message": f"'{request.symbol}' is not a valid NSE/BSE listed company symbol",
                "provided_symbol": request.symbol
            }
            
            # Add suggestions if we found any
            if suggestions:
                error_detail["suggestions"] = [
                    f"{s['symbol']} ({s['name']})" for s in suggestions
                ]
            else:
                error_detail["example_valid_symbols"] = ["TCS", "RELIANCE", "INFY", "HDFCBANK"]
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        # Format the symbol properly (uppercase, trimmed)
        validated_symbol = stock_validator.validate_and_format_symbol(request.symbol)
        print(f"✅ Symbol validated: {validated_symbol}")
        # ====== END VALIDATION STEP ======
        
        # Step 1: Check cache first (10-minute rule)
        print(f"🔍 Checking cache for symbol: {validated_symbol}")
        cached_news = get_cached_news(db, validated_symbol, settings.CACHE_EXPIRY_MINUTES)
        
        if cached_news:
            print(f"✅ Found cached data for {validated_symbol}")
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
        print(f"📰 Fetching fresh news for {validated_symbol}")
        news_articles = await news_service.fetch_news(validated_symbol)
        
        if not news_articles:
            # Since symbol is valid, this is just no news found
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "No news found",
                    "message": f"No recent news found for {validated_symbol}. This is a valid stock symbol but no recent news articles are available.",
                    "symbol": validated_symbol
                }
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
        news_record = save_news_record(db, validated_symbol, headlines_with_sentiment)
        
        # Step 5: Format response
        response_headlines = [
            HeadlineWithSentiment(
                title=headline["title"],
                sentiment=headline["sentiment"]
            )
            for headline in headlines_with_sentiment
        ]
        
        print(f"🎉 Successfully processed {validated_symbol}")
        return NewsResponse(
            symbol=validated_symbol,
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
        # ====== VALIDATION FOR GET ENDPOINT TOO ======
        if not stock_validator.is_valid_symbol(symbol):
            suggestions = stock_validator.get_suggestions(symbol, limit=3)
            error_detail = {
                "error": "Invalid stock symbol",
                "message": f"'{symbol}' is not a valid NSE/BSE listed company symbol",
                "provided_symbol": symbol
            }
            
            if suggestions:
                error_detail["suggestions"] = [
                    f"{s['symbol']} ({s['name']})" for s in suggestions
                ]
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        validated_symbol = stock_validator.validate_and_format_symbol(symbol)
        # ====== END VALIDATION ======
        
        cached_news = get_cached_news(db, validated_symbol, cache_minutes=60)  # Check last hour
        
        if not cached_news:
            raise HTTPException(
                status_code=404,
                detail=f"No cached data found for symbol: {validated_symbol}"
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

# ====== NEW ENDPOINT: Get Valid Symbols ======
@router.get("/valid-symbols")
async def get_valid_symbols():
    """
    Get list of all valid stock symbols for reference.
    Useful for frontend dropdown or validation.
    """
    try:
        return {
            "valid_symbols": stock_validator.valid_stocks,
            "total_count": len(stock_validator.valid_stocks),
            "message": "List of supported Indian stock symbols"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving valid symbols: {str(e)}"
        )