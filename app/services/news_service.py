# app/services/news_service.py
import aiohttp
import asyncio
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import NewsArticle
from utils.config import settings

class NewsService:
    def __init__(self):
        self.rapidapi_key = settings.RAPIDAPI_KEY
        self.rapidapi_host = settings.RAPIDAPI_HOST
        self.max_articles = settings.MAX_NEWS_ARTICLES
        
    async def fetch_news(self, symbol: str) -> List[NewsArticle]:
        """
        Fetch news articles for a given stock symbol using RapidAPI Bing News
        """
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        # Search query for Indian stock news
        search_query = f"{symbol} stock India news"
        
        # FIXED: Correct URL for News Search endpoint
        url = "https://bing-news-search1.p.rapidapi.com/news/search"
        
        # FIXED: Updated headers to match RapidAPI News Search exactly
        headers = {
            'x-rapidapi-key': self.rapidapi_key,
            'x-rapidapi-host': self.rapidapi_host,
            'X-BingApis-SDK': 'true'
        }
        
        params = {
            'freshness': 'Day',
            'textFormat': 'Raw', 
            'safeSearch': 'Off',
            'q': search_query,
            'count': self.max_articles
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"🌐 Calling RapidAPI for symbol: {symbol}")
                print(f"🔍 Search query: {search_query}")
                print(f"📡 URL: {url}")
                print(f"📋 Params: {params}")
                
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📊 API Response Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API call successful!")
                        return self._parse_news_response(data)
                    elif response.status == 401:
                        raise ValueError("Invalid RapidAPI key or subscription expired")
                    elif response.status == 429:
                        raise ValueError("RapidAPI rate limit exceeded")
                    elif response.status == 403:
                        raise ValueError("RapidAPI access forbidden - check your subscription")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error response: {error_text}")
                        raise ValueError(f"RapidAPI error: {response.status} - {error_text}")
                        
        except aiohttp.ClientError as e:
            print(f"❌ Network error calling RapidAPI: {e}")
            raise ValueError(f"Network error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error calling RapidAPI: {e}")
            raise ValueError(f"API error: {str(e)}")
    
    def _parse_news_response(self, data: dict) -> List[NewsArticle]:
        """
        Parse the RapidAPI Bing News response into NewsArticle objects
        """
        articles = []
        
        # Bing News API response structure
        news_items = data.get("value", [])
        
        print(f"📰 Found {len(news_items)} news articles")
        
        for item in news_items[:self.max_articles]:  # Limit to max articles
            try:
                title = item.get("name", "").strip()
                url = item.get("url", "")
                published_date = item.get("datePublished", "")
                
                # Get source name
                provider = item.get("provider", [])
                source = provider[0].get("name", "Unknown") if provider else "Unknown"
                
                if title:  # Only add if title exists
                    article = NewsArticle(
                        title=title,
                        url=url,
                        published_date=published_date,
                        source=source
                    )
                    articles.append(article)
                    print(f"  ✓ Added: {title[:60]}...")
                
            except Exception as e:
                print(f"  ✗ Error parsing article: {e}")
                continue
        
        if not articles:
            print("⚠️  No valid articles found in API response")
            
        return articles
    
    async def test_api_connection(self) -> bool:
        """
        Test the RapidAPI connection with a simple query
        """
        try:
            articles = await self.fetch_news("TCS")  # Test with TCS
            return len(articles) > 0
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False

# Simple test function to verify the fix
async def test_news_service():
    """Test the news service with correct URL"""
    
    # Mock settings for testing
    class MockSettings:
        RAPIDAPI_KEY = "3bab928451msh6ed9e0fce363b61p140892jsnc3d7edbde81a"
        RAPIDAPI_HOST = "bing-news-search1.p.rapidapi.com"
        MAX_NEWS_ARTICLES = 3
    
    # Temporarily replace settings
    import utils.config
    original_settings = utils.config.settings
    utils.config.settings = MockSettings()
    
    try:
        news_service = NewsService()
        print("🧪 Testing News Service with corrected URL...")
        
        # Test the connection
        articles = await news_service.fetch_news("TCS")
        
        if articles:
            print(f"✅ SUCCESS! Retrieved {len(articles)} articles")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article.title[:80]}...")
        else:
            print("⚠️  No articles found, but API call succeeded")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Restore original settings
        utils.config.settings = original_settings

# Fallback/Mock service for testing without API key
class MockNewsService:
    """Mock news service for testing when API key is not available"""
    
    async def fetch_news(self, symbol: str) -> List[NewsArticle]:
        """Return mock news articles for testing"""
        mock_articles = [
            NewsArticle(
                title=f"{symbol} reports strong quarterly growth in latest earnings",
                url="https://example.com/news1",
                published_date="2025-07-31T10:00:00Z",
                source="Mock Financial Times"
            ),
            NewsArticle(
                title=f"Market analysts upgrade {symbol} stock rating to buy",
                url="https://example.com/news2", 
                published_date="2025-07-31T08:30:00Z",
                source="Mock Business Today"
            ),
            NewsArticle(
                title=f"Tech sector volatility affects {symbol} trading volumes",
                url="https://example.com/news3",
                published_date="2025-07-31T07:15:00Z", 
                source="Mock Economic Times"
            )
        ]
        
        print(f"🧪 Using mock news service for {symbol}")
        return mock_articles[:settings.MAX_NEWS_ARTICLES]

# Run test if this file is executed directly
if __name__ == "__main__":
    asyncio.run(test_news_service())