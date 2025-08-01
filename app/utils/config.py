# app/utils/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Password123@localhost:5432/news_sentiment")
    
    # RapidAPI Configuration
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
    RAPIDAPI_HOST: str = os.getenv("RAPIDAPI_HOST", "bing-news-search1.p.rapidapi.com")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Configuration
    APP_NAME: str = "News Sentiment API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Cache Configuration
    CACHE_EXPIRY_MINUTES: int = 10
    
    # News API Configuration
    MAX_NEWS_ARTICLES: int = 3
    
    def validate_settings(self):
        """Validate that all required environment variables are set"""
        missing_vars = []
        
        if not self.RAPIDAPI_KEY:
            missing_vars.append("RAPIDAPI_KEY")
        
        if not self.OPENAI_API_KEY:
            missing_vars.append("OPENAI_API_KEY")
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Create a global settings instance
settings = Settings()

# Validate settings when module is imported (optional - you can remove this for now)
# settings.validate_settings()