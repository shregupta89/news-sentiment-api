#  News Sentiment API

A FastAPI-based service that fetches news headlines for Indian stock symbols, performs sentiment analysis using OpenAI's GPT-3.5 Turbo, and stores results in a PostgreSQL database with intelligent caching.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [API Examples](#api-examples)
- [Development & Debugging](#development--debugging)
- [Configuration](#configuration)
- [AI Tools Usage](#ai-tools-usage)
- [Contributing](#contributing)

## Overview

This API accepts a stock symbol, fetches 2-3 recent news headlines, analyzes their sentiment, and returns a comprehensive sentiment summary. The service implements intelligent caching to avoid redundant API calls within a 10-minute window.

### Key Features
- ✅ Real-time news fetching for Indian stock symbols
- ✅ AI-powered sentiment analysis using OpenAI GPT-3.5 Turbo
- ✅ PostgreSQL database with Docker containerization
- ✅ 10-minute intelligent caching mechanism
- ✅ RESTful API with FastAPI
- ✅ Comprehensive error handling and logging

##  Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI |
| **Database** | PostgreSQL |
| **News Source** | Google News API (via RapidAPI) |
| **Sentiment Analysis** | OpenAI GPT-3.5 Turbo |
| **Containerization** | Docker & Docker Compose |
| **ORM** | SQLAlchemy |
| **Validation** | Pydantic |

##  Project Structure

```
news-sentiment-api/
├── .env                          # Environment variables (API keys, DB config)
├── .env.sample                   # Sample environment file
├── .gitignore                    # Git ignore file
├── docker-compose.yml            # PostgreSQL container setup
├── Dockerfile                    # Application containerization
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
│
├── app/                          # Main application directory
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   │
│   ├── api/                      # API routes and endpoints
│   │   ├── __init__.py
│   │   └── routes.py             # POST /news-sentiment endpoint
│   │
│   ├── models/                   # Database models and schemas
│   │   ├── __init__.py
│   │   ├── database.py           # Database connection setup
│   │   └── schemas.py            # Pydantic models for request/response
│   │
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── news_service.py       # Google News API integration
│   │   ├── sentiment_service.py  # OpenAI sentiment analysis
│   │   └── cache_service.py      # 10-minute caching logic
│   │
│   └── utils/                    # Utility functions and config
│       ├── __init__.py
│       └── config.py             # Configuration management
```

##  Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ (for local development)
- API keys for Google News (RapidAPI) and OpenAI

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/news-sentiment-api.git
cd news-sentiment-api
```

### 2. Environment Configuration
Create a `.env` file based on `.env.sample`:

```bash
cp .env.sample .env
```

Update the `.env` file with your API keys:
```env
DATABASE_URL=postgresql://user:password123@localhost:5432/news_sentiment
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=google-news13.p.rapidapi.com
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=true
```

### 3. Docker Setup (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Local Development Setup (Alternative)
```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL container only
docker-compose up db -d

# Run the FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/
- Database: localhost:5432

## 📖 API Documentation

### POST /news-sentiment

Fetches news headlines for a stock symbol and analyzes sentiment.

![API Documentation](https://github.com/user-attachments/assets/6f66665d-1746-454e-b440-35bc631ecc02)


**Request:**
```json
{
  "symbol": "TCS"
}
```

**Response:**
```json
{
  "symbol": "TCS",
  "timestamp": "2025-08-02T18:00:00Z",
  "headlines": [
    {
      "title": "TCS reports strong Q1 growth with 15% revenue increase",
      "sentiment": "positive"
    },
    {
      "title": "IT sector faces macro uncertainty amid global slowdown",
      "sentiment": "negative"
    },
    {
      "title": "TCS announces new AI initiative for enterprise clients",
      "sentiment": "neutral"
    }
  ],
  "overall_sentiment": "neutral",
  "cached": false
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid stock symbol
- `404`: No news found
- `422`: Validation error
- `500`: Internal server error

### Interactive Documentation
Visit http://localhost:8000/docs for Swagger UI documentation with interactive API testing.

## 🧪 API Examples

### Successful Response (Valid Symbol)
When you provide a valid Indian stock symbol, the API returns news headlines with sentiment analysis:

![Valid Symbol Response](https://github.com/user-attachments/assets/75cefbd2-d551-4996-87ec-68beff8e149f)

### Error Handling (Invalid Symbol)
The API validates stock symbols and provides helpful error messages with suggestions:

![Invalid Symbol Error](https://github.com/user-attachments/assets/62bc0c06-e4ea-475e-9d1e-3decd100f0c9)

### Additional Endpoints

**GET /valid-symbols** - Get all supported stock symbols:
```bash
curl "http://localhost:8000/valid-symbols"
```

**GET /news-sentiment/{symbol}** - Get cached data for a symbol:
```bash
curl "http://localhost:8000/news-sentiment/TCS"
```

## 🛠️ Development & Debugging

### Backend Logs
The application provides comprehensive logging for debugging and monitoring:

![Backend Logs](https://github.com/user-attachments/assets/84020f9b-c809-4ab9-806c-db76b368430c)

### Log Features:
- ✅ **Symbol Validation**: Track validation success/failure
- 📰 **News Fetching**: Monitor API calls and response status  
- 🤖 **Sentiment Analysis**: Progress tracking for each headline
- 💾 **Database Operations**: Cache hits/misses and data persistence
- ⚡ **Performance**: Response times and error tracking
- 🔍 **Request Tracing**: Complete request lifecycle visibility

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `RAPIDAPI_KEY` | RapidAPI key for Google News | Yes |
| `RAPIDAPI_HOST` | RapidAPI host for Google News | Yes |
| `OPENAI_API_KEY` | OpenAI API key for sentiment analysis | Yes |
| `DEBUG` | Enable debug mode | No |

### Caching Behavior
- Results are cached for **10 minutes** per stock symbol
- Subsequent requests within this window return cached data
- Cache status is indicated in the API response

## 🤖 AI Tools Usage

This project was built with extensive use of AI tools to accelerate development:

### Development Process
1. **Initial Architecture**: Used Claude/ChatGPT to design the FastAPI project structure and best practices
2. **Database Schema**: AI-assisted design of PostgreSQL tables and SQLAlchemy models  
3. **API Integration**: Generated boilerplate code for Google News API and OpenAI integration
4. **Error Handling**: AI-powered comprehensive error handling and logging implementation
5. **Docker Configuration**: AI-assisted Docker and docker-compose setup
6. **Testing**: Generated test cases and validation logic

### AI-Generated Components
- FastAPI route structure and middleware setup
- Pydantic schemas for request/response validation
- Database connection and session management
- Caching logic implementation
- OpenAI prompt engineering for sentiment analysis
- Docker containerization configuration

### Manual Refinements
- Fine-tuned sentiment analysis prompts for financial news
- Optimized database queries and indexing
- Enhanced error messages and user experience
- Custom business logic for Indian stock symbols

## 🧪 News & Sentiment Implementation

### News Fetching
- **Source**: Google News API via RapidAPI
- **Query Strategy**: Uses stock symbol + "NSE" or "BSE" for Indian market relevance
- **Filtering**: Extracts 2-3 most recent and relevant headlines
- **Fallback**: Graceful handling of API rate limits and errors

### Sentiment Analysis
- **Model**: OpenAI GPT-3.5 Turbo
- **Approach**: Custom prompts optimized for financial news sentiment
- **Output**: Three-class classification (positive, negative, neutral)
- **Confidence**: Includes reasoning in API logs for transparency
- **Aggregation**: Overall sentiment calculated using majority vote with neutral bias

### Sample Prompts Used
```
Analyze the sentiment of this financial news headline: "{headline}"
Return only one word: "positive", "negative", or "neutral"
Consider the impact on stock price and investor sentiment.
```

## 🐳 Docker Services

### Application Container (`fastapi-backend`)
- Based on Python 3.9 slim image
- Runs on port 8000
- Auto-reloads on code changes (development)
- Depends on PostgreSQL service

### Database Container (`postgres-db`)
- PostgreSQL latest image
- Persistent data storage
- Pre-configured with database and credentials
- Accessible on port 5432

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [OpenAI](https://openai.com/) for sentiment analysis capabilities
- [RapidAPI](https://rapidapi.com/) for news API access
- AI tools (ChatGPT, Claude) for development acceleration

---

**Built with ❤️ for the Diversifi Backend Assignment**
