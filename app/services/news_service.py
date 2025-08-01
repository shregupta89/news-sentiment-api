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
        self.rapidapi_host = "google-news13.p.rapidapi.com"  # Fixed host for Google News API
        self.max_articles = settings.MAX_NEWS_ARTICLES
        
    async def fetch_news(self, symbol: str) -> List[NewsArticle]:
        """
        Fetch news articles for a given Indian stock symbol using Google News API
        """
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        # Search query specifically for Indian stock news
        search_keyword = f"{symbol} stock India NSE BSE share price"
        
        # Use the /search endpoint from Google News API
        url = f"https://{self.rapidapi_host}/search"
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }
        
        params = {
            "keyword": search_keyword,
            "lr": "en-IN"  # English, India region for Indian stock news
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"🌐 Calling Google News API for symbol: {symbol}")
                print(f"🔍 Search keyword: {search_keyword}")
                
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📡 API Response Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_google_news_response(data, symbol)
                    elif response.status == 401:
                        raise ValueError("Invalid RapidAPI key or subscription expired")
                    elif response.status == 429:
                        raise ValueError("RapidAPI rate limit exceeded")
                    elif response.status == 403:
                        raise ValueError("RapidAPI access forbidden - check your subscription")
                    else:
                        response_text = await response.text()
                        print(f"❌ API Error Response: {response_text}")
                        raise ValueError(f"Google News API error: {response.status} - {response_text}")
                        
        except aiohttp.ClientError as e:
            print(f"❌ Network error calling Google News API: {e}")
            raise ValueError(f"Network error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error calling Google News API: {e}")
            raise ValueError(f"API error: {str(e)}")
    
    def _parse_google_news_response(self, data: dict, symbol: str) -> List[NewsArticle]:
        """
        Parse the Google News API response into NewsArticle objects
        """
        articles = []
        
        # Google News API response structure - check for different possible formats
        if isinstance(data, dict):
            # Try different possible response formats
            news_items = data.get("items", data.get("articles", data.get("data", [])))
            
            # If it's a direct list
            if isinstance(data, list):
                news_items = data
            elif "items" in data:
                news_items = data["items"]
            elif "articles" in data:
                news_items = data["articles"] 
            else:
                # Sometimes the response is directly the articles list
                news_items = data if isinstance(data, list) else []
        else:
            news_items = data if isinstance(data, list) else []
        
        print(f"📰 Found {len(news_items)} news items from Google News")
        
        # Filter and process articles
        processed_count = 0
        for item in news_items:
            if processed_count >= self.max_articles:
                break
                
            try:
                # Handle different possible field names from Google News API
                title = (
                    item.get("title", "") or 
                    item.get("headline", "") or 
                    item.get("name", "")
                ).strip()
                
                # Only process if title exists and contains stock-related keywords
                if title and self._is_stock_related(title, symbol):
                    url = item.get("url", item.get("link", ""))
                    published_date = item.get("published", item.get("publishedAt", item.get("date", "")))
                    source = item.get("source", item.get("publisher", "Google News"))
                    
                    # Extract source name if it's an object
                    if isinstance(source, dict):
                        source = source.get("name", "Google News")
                    
                    article = NewsArticle(
                        title=title,
                        url=url,
                        published_date=str(published_date),
                        source=str(source)
                    )
                    articles.append(article)
                    processed_count += 1
                    print(f"  ✓ Added: {title[:60]}...")
                
            except Exception as e:
                print(f"  ✗ Error parsing article: {e}")
                continue
        
        if not articles:
            print("⚠️  No relevant stock articles found in API response")
            # If no articles found, create a fallback search with just the symbol
            if processed_count == 0 and news_items:
                print("🔄 Trying to get any available headlines...")
                for item in news_items[:self.max_articles]:
                    try:
                        title = (
                            item.get("title", "") or 
                            item.get("headline", "") or 
                            item.get("name", "")
                        ).strip()
                        
                        if title:
                            url = item.get("url", item.get("link", ""))
                            published_date = item.get("published", item.get("publishedAt", item.get("date", "")))
                            source = item.get("source", item.get("publisher", "Google News"))
                            
                            if isinstance(source, dict):
                                source = source.get("name", "Google News")
                            
                            article = NewsArticle(
                                title=title,
                                url=url,
                                published_date=str(published_date),
                                source=str(source)
                            )
                            articles.append(article)
                            print(f"  ✓ Fallback: {title[:60]}...")
                    except:
                        continue
            
        return articles
    
    def _is_stock_related(self, title: str, symbol: str) -> bool:
        """
        Check if the title is related to the stock symbol or general stock market
        """
        title_lower = title.lower()
        symbol_lower = symbol.lower()
        
        # Stock-specific keywords
        stock_keywords = [
            symbol_lower, 'stock', 'share', 'equity', 'nse', 'bse', 
            'market', 'trading', 'investor', 'price', 'earnings',
            'profit', 'revenue', 'quarterly', 'financial', 'dividend'
        ]
        
        # Check if title contains the symbol or stock-related keywords
        return (
            symbol_lower in title_lower or
            any(keyword in title_lower for keyword in stock_keywords)
        )
    
    async def test_api_connection(self) -> bool:
        """
        Test the Google News API connection with a simple query
        """
        try:
            articles = await self.fetch_news("TCS")  # Test with TCS
            return len(articles) > 0
        except Exception as e:
            print(f"❌ Google News API test failed: {e}")
            return False

# Fallback/Mock service for testing without API key
# class MockNewsService:
#     """Mock news service for testing when API key is not available"""
    
#     async def fetch_news(self, symbol: str) -> List[NewsArticle]:
#         """Return mock news articles for testing"""
#         mock_articles = [
#             NewsArticle(
#                 title=f"{symbol} reports strong quarterly growth in latest earnings",
#                 url="https://example.com/news1",
#                 published_date="2025-07-31T10:00:00Z",
#                 source="Mock Financial Times"
#             ),
#             NewsArticle(
#                 title=f"Market analysts upgrade {symbol} stock rating to buy",
#                 url="https://example.com/news2", 
#                 published_date="2025-07-31T08:30:00Z",
#                 source="Mock Business Today"
#             ),
#             NewsArticle(
#                 title=f"Tech sector volatility affects {symbol} trading volumes",
#                 url="https://example.com/news3",
#                 published_date="2025-07-31T07:15:00Z", 
#                 source="Mock Economic Times"
#             )
#         ]
        
#         print(f"🧪 Using mock news service for {symbol}")
#         return mock_articles[:settings.MAX_NEWS_ARTICLES]