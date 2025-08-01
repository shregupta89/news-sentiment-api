#!/usr/bin/env python3
"""
Test script using the exact News Search endpoint format from RapidAPI
"""

import http.client
import json
import urllib.parse

def test_news_search_basic():
    """Test 1: Basic news search (from RapidAPI example)"""
    print("🔍 Test 1: Basic News Search")
    print("-" * 30)
    
    conn = http.client.HTTPSConnection("bing-news-search1.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "3bab928451msh6ed9e0fce363b61p140892jsnc3d7edbde81a",
        'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
        'X-BingApis-SDK': "true"
    }

    try:
        conn.request("GET", "/news/search?freshness=Day&textFormat=Raw&safeSearch=Off", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        print(f"📊 Status Code: {res.status}")
        print(f"📋 Response Headers: {dict(res.getheaders())}")
        
        if res.status == 200:
            response_text = data.decode("utf-8")
            try:
                json_data = json.loads(response_text)
                articles = json_data.get("value", [])
                print(f"✅ SUCCESS! Found {len(articles)} articles")
                
                if articles:
                    print("\n📰 Sample Articles:")
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get('name', 'No title')[:80]
                        source = article.get('provider', [{}])[0].get('name', 'Unknown') if article.get('provider') else 'Unknown'
                        print(f"  {i}. {title}... (Source: {source})")
                        
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response_text[:200]}...")
        else:
            print(f"❌ Error {res.status}: {data.decode('utf-8')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        conn.close()

def test_news_search_with_query():
    """Test 2: News search with specific query (TCS stock)"""
    print("\n🔍 Test 2: TCS Stock News Search")
    print("-" * 30)
    
    conn = http.client.HTTPSConnection("bing-news-search1.p.rapidapi.com")

    headers = {
        'x-rapidapi-key': "3bab928451msh6ed9e0fce363b61p140892jsnc3d7edbde81a",
        'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
        'X-BingApis-SDK': "true"
    }

    # URL encode the search query
    search_query = "TCS stock India news"
    encoded_query = urllib.parse.quote(search_query)
    
    endpoint = f"/news/search?freshness=Day&textFormat=Raw&safeSearch=Off&q={encoded_query}&count=3"
    
    try:
        print(f"🔗 Endpoint: {endpoint}")
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        print(f"📊 Status Code: {res.status}")
        
        if res.status == 200:
            response_text = data.decode("utf-8")
            try:
                json_data = json.loads(response_text)
                articles = json_data.get("value", [])
                print(f"✅ SUCCESS! Found {len(articles)} TCS articles")
                
                if articles:
                    print("\n📰 TCS News Articles:")
                    for i, article in enumerate(articles, 1):
                        title = article.get('name', 'No title')
                        url = article.get('url', 'No URL')
                        date = article.get('datePublished', 'No date')
                        source = article.get('provider', [{}])[0].get('name', 'Unknown') if article.get('provider') else 'Unknown'
                        
                        print(f"  {i}. {title}")
                        print(f"     Source: {source} | Date: {date}")
                        print(f"     URL: {url}")
                        print()
                else:
                    print("⚠️  No articles found for TCS")
                        
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response_text[:200]}...")
        else:
            error_text = data.decode("utf-8")
            print(f"❌ Error {res.status}: {error_text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        conn.close()

def test_with_aiohttp():
    """Test 3: Same test but with aiohttp (like your service)"""
    import asyncio
    import aiohttp
    
    async def aiohttp_test():
        print("\n🔍 Test 3: Using aiohttp (like your service)")
        print("-" * 40)
        
        url = "https://bing-news-search1.p.rapidapi.com/news/search"
        
        headers = {
            'x-rapidapi-key': "3bab928451msh6ed9e0fce363b61p140892jsnc3d7edbde81a",
            'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
            'X-BingApis-SDK': 'true'
        }
        
        params = {
            'freshness': 'Day',
            'textFormat': 'Raw',
            'safeSearch': 'Off',
            'q': 'TCS stock India news',
            'count': 3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📊 Status Code: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get("value", [])
                        print(f"✅ aiohttp SUCCESS! Found {len(articles)} articles")
                    else:
                        error_text = await response.text()
                        print(f"❌ aiohttp Error {response.status}: {error_text}")
                        
        except Exception as e:
            print(f"❌ aiohttp Exception: {e}")
    
    # Run the async test
    asyncio.run(aiohttp_test())

if __name__ == "__main__":
    print("🧪 Testing RapidAPI Bing News Search - News Search Endpoint")
    print("=" * 60)
    
    # Test basic functionality
    test_news_search_basic()
    
    # Test with specific query
    test_news_search_with_query()
    
    # Test with aiohttp 
    test_with_aiohttp()
    
    print("\n" + "="*60)
    print("💡 Summary:")
    print("✅ If all tests pass → Your API key is working!")
    print("❌ If 401/403 → Check API key or subscription")
    print("❌ If 404 → Endpoint issue")
    print("❌ If 429 → Rate limit hit")
    print("\n🔗 Manage subscription: https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/bing-news-search1")