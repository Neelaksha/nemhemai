# Search Routes
import requests
from fastapi import FastAPI, HTTPException, Query
from config import EXA_API_KEY, TAVILY_API_KEY

def register_search_routes(app: FastAPI):
    
    @app.get("/search/searxng")
    def searxng_search(query: str = Query(..., description="Search query"), max_results: int = 5):
        """Search using local SearxNG instance."""
        searxng_url = "http://localhost:8888/search"
        
        params = {
            "q": query,
            "format": "json",
            "categories": "general",
            "engines": "google,bing,duckduckgo",
            "pageno": 1
        }
        
        try:
            response = requests.get(searxng_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for result in data.get("results", [])[:max_results]:
                results.append({
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "engine": result.get("engine", "")
                })
            
            return {"results": results, "query": query}
            
        except Exception as e:
            return {"error": str(e), "results": []}

    @app.get("/search/web")
    def exa_web_search(query: str = Query(..., description="Search query")):
        if not EXA_API_KEY:
            return {"error": "EXA_API_KEY not set in environment variables."}
        url = "https://api.exa.ai/search"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {EXA_API_KEY}"
        }
        payload = {
            "query": query,
            "numResults": 5
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/search/youtube")
    def tavily_youtube_search(query: str = Query(..., description="Search query"), max_results: int = 5):
        """Search YouTube videos using Tavily API."""
        if not TAVILY_API_KEY:
            return {"error": "TAVILY_API_KEY not set in environment variables."}
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        payload = {
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_sources": True,
            "search_type": "youtube"
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print("Tavily YouTube response:", response.text)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/search/reddit")
    def tavily_reddit_search(query: str = Query(..., description="Search query"), max_results: int = 5):
        """Search Reddit posts using Tavily API."""
        if not TAVILY_API_KEY:
            return {"error": "TAVILY_API_KEY not set in environment variables."}
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        payload = {
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_sources": True,
            "search_type": "reddit"
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print("Tavily Reddit response:", response.text)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/search/academic")
    def tavily_academic_search(query: str = Query(..., description="Search query"), max_results: int = 5):
        """Search academic papers using Tavily API."""
        if not TAVILY_API_KEY:
            return {"error": "TAVILY_API_KEY not set in environment variables."}
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        payload = {
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_sources": True,
            "search_type": "academic"
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print("Tavily Academic response:", response.text)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/search/crypto")
    def tavily_crypto_search(query: str = Query(..., description="Search query"), max_results: int = 5):
        """Search crypto news using Tavily API."""
        if not TAVILY_API_KEY:
            return {"error": "TAVILY_API_KEY not set in environment variables."}
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        payload = {
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_sources": True,
            "search_type": "crypto"
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            print("Tavily Crypto response:", response.text)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}