# app/services/sentiment_service.py
import openai
from typing import Literal
import sys
import os
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import settings

SentimentType = Literal["positive", "negative", "neutral"]

class SentimentService:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
    async def analyze_sentiment(self, headline: str) -> SentimentType:
        """
        Analyze sentiment of a news headline using OpenAI API
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        if not headline or headline.strip() == "":
            return "neutral"
        
        try:
            # Create a focused prompt for financial news sentiment
            prompt = self._create_sentiment_prompt(headline)
            
            print(f"🤖 Analyzing sentiment for: '{headline[:50]}...'")
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            # Parse and validate response
            sentiment = self._parse_sentiment_response(response)
            
            print(f"  📊 Sentiment result: {sentiment}")
            return sentiment
            
        except Exception as e:
            print(f"❌ Error analyzing sentiment: {e}")
            # Fallback to rule-based sentiment if OpenAI fails
            return self._fallback_sentiment_analysis(headline)
    
    def _create_sentiment_prompt(self, headline: str) -> str:
        """Create an optimized prompt for financial news sentiment analysis"""
        return f"""Analyze the sentiment of this financial news headline about an Indian stock.

Headline: "{headline}"

Instructions:
- Consider financial and market context
- Focus on impact on stock price/company performance
- Return ONLY one word: positive, negative, or neutral
- Positive: Good news for the company/stock (growth, profits, upgrades, deals, etc.)
- Negative: Bad news for the company/stock (losses, downgrades, problems, etc.)  
- Neutral: Factual reporting without clear positive/negative impact

Response:"""

    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with error handling"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Cost-effective model
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=10,  # We only need one word
                temperature=0.1,  # Low temperature for consistent results
                timeout=10  # 10 second timeout
            )
            
            return response.choices[0].message.content.strip().lower()
            
        except openai.error.RateLimitError:
            raise ValueError("OpenAI rate limit exceeded")
        except openai.error.AuthenticationError:
            raise ValueError("Invalid OpenAI API key")
        except openai.error.APIError as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"OpenAI request failed: {str(e)}")
    
    def _parse_sentiment_response(self, response: str) -> SentimentType:
        """Parse and validate OpenAI response"""
        if not response:
            return "neutral"
        
        # Clean the response
        response = response.strip().lower()
        
        # Extract sentiment word using regex
        sentiment_match = re.search(r'\b(positive|negative|neutral)\b', response)
        
        if sentiment_match:
            sentiment = sentiment_match.group(1)
            if sentiment in ["positive", "negative", "neutral"]:
                return sentiment
        
        # If no clear sentiment found, try keyword matching
        if any(word in response for word in ["positive", "good", "up", "growth", "gain"]):
            return "positive"
        elif any(word in response for word in ["negative", "bad", "down", "loss", "decline"]):
            return "negative"
        else:
            return "neutral"
    
    def _fallback_sentiment_analysis(self, headline: str) -> SentimentType:
        """
        Simple rule-based sentiment analysis as fallback
        when OpenAI API is not available or fails
        """
        headline_lower = headline.lower()
        
        # Positive keywords for financial news
        positive_keywords = [
            'growth', 'profit', 'gain', 'rise', 'increase', 'up', 'surge', 'rally',
            'strong', 'robust', 'positive', 'upgrade', 'buy', 'expansion', 'deal',
            'acquisition', 'revenue', 'earnings beat', 'outperform', 'bullish'
        ]
        
        # Negative keywords for financial news  
        negative_keywords = [
            'loss', 'decline', 'fall', 'drop', 'down', 'crash', 'plunge', 'slump',
            'weak', 'poor', 'negative', 'downgrade', 'sell', 'layoffs', 'lawsuit',
            'scandal', 'miss', 'underperform', 'bearish', 'recession', 'crisis'
        ]
        
        positive_score = sum(1 for keyword in positive_keywords if keyword in headline_lower)
        negative_score = sum(1 for keyword in negative_keywords if keyword in headline_lower)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"
    
    async def analyze_batch_sentiment(self, headlines: list[str]) -> list[SentimentType]:
        """
        Analyze sentiment for multiple headlines efficiently
        Could be optimized to send multiple headlines in one API call
        """
        results = []
        for headline in headlines:
            sentiment = await self.analyze_sentiment(headline)
            results.append(sentiment)
        return results
    
    async def test_api_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            test_sentiment = await self.analyze_sentiment("Test headline for API connection")
            return test_sentiment in ["positive", "negative", "neutral"]
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
            return False

# Mock sentiment service for testing
class MockSentimentService:
    """Mock sentiment service for testing without OpenAI API key"""
    
    async def analyze_sentiment(self, headline: str) -> SentimentType:
        """Return mock sentiment based on simple keyword matching"""
        headline_lower = headline.lower()
        
        if any(word in headline_lower for word in ['strong', 'growth', 'profit', 'buy', 'upgrade']):
            return "positive"
        elif any(word in headline_lower for word in ['weak', 'loss', 'decline', 'sell', 'downgrade']):
            return "negative"
        else:
            return "neutral"