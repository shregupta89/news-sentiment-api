# app/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

# Request Models
class NewsRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., TCS, INFY)")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Symbol cannot be empty')
        # Convert to uppercase and remove whitespace
        return v.strip().upper()

# Response Models
class HeadlineWithSentiment(BaseModel):
    title: str = Field(..., description="News headline title")
    sentiment: str = Field(..., description="Sentiment: positive, negative, or neutral")

class NewsResponse(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    timestamp: datetime = Field(..., description="Timestamp when data was fetched")
    headlines: List[HeadlineWithSentiment] = Field(..., description="List of headlines with sentiment")
    
    class Config:
        # This allows the model to work with SQLAlchemy objects
        from_attributes = True
        # Example for API documentation
        json_schema_extra = {
            "example": {
                "symbol": "TCS",
                "timestamp": "2025-07-29T18:00:00Z",
                "headlines": [
                    {
                        "title": "TCS reports strong Q1 growth",
                        "sentiment": "positive"
                    },
                    {
                        "title": "IT sector faces macro uncertainty", 
                        "sentiment": "negative"
                    }
                ]
            }
        }

# Internal Models (for service layer)
class NewsArticle(BaseModel):
    """Internal model for raw news articles before sentiment analysis"""
    title: str
    url: str = ""
    published_date: str = ""
    source: str = ""

class SentimentResult(BaseModel):
    """Internal model for sentiment analysis results"""
    text: str
    sentiment: str  # positive, negative, neutral
    confidence: float = 0.0  # Optional confidence score

# Database Models (for converting SQLAlchemy to Pydantic)
class NewsRecordDB(BaseModel):
    id: int
    symbol: str
    timestamp: datetime
    headlines: List[dict]  # JSON field from database
    created_at: datetime
    
    class Config:
        from_attributes = True

# What is Pydantic Schema?
# Pydantic schemas are data validation and documentation models that define:
# What data comes INTO your API (requests)
# What data goes OUT of your API (responses)
# How to validate and convert that data