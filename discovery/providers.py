import os
import asyncio
import httpx
from typing import List, Dict

# Which web search backend to use: "bing" (default) or "serpapi"
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "bing").lower()
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")

class SearchResult(dict):
    """Simple alias for typed results."""
    pass

async def bing_search(query: str, limit: int = 20) -> List[SearchResult]:
    """
    Bing Web Search API v7 style.
    Requires: env SEARCH_API_KEY to be set to your Bing key.
    Docs: https://learn.microsoft.com/bing/search-apis/bing-web-search/reference/endpoints
    """
    if not SEARCH_API_KEY:
        return []
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": SEARCH_API_KEY}
    params = {
        "q": query,
        "count": limit,
        "responseFilter": "Webpages",
        # optional: "mkt": "en-US",
        # optional: "safeSearch": "Moderate"
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        items = []
        for w in (data.get("webPages", {}) or {}).get("value", []):
            items.append({
                "name": w.get("name"),
                "url": w.get("url"),
                "snippet": w.get("snippet")
            })
        return items

async def serpapi_search(query: str, limit: int = 20) -> List[SearchResult]:
    """
    SerpAPI Google search.
    Requires: env SEARCH_API_KEY to be set to your SerpAPI key.
    Docs: https://serpapi.com/search-api
    """
    if not SEARCH_API_KEY:
        return []
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "num": limit,
        "api_key": SEARCH_API_KEY
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        items = []
        for w in data.get("organic_results", []):
            items.append({
                "name": w.get("title"),
                "url": w.get("link"),
                "snippet": w.get("snippet")
            })
        return items

async def web_search(query: str, limit: int = 20) -> List[SearchResult]:
    """Selects the configured provider and runs a web search."""
    if SEARCH_PROVIDER == "serpapi":
        return await serpapi_search(query, limit)
    # default
    return await bing_search(query, limit)
