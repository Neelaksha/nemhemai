import requests

# Test SearxNG directly
searxng_url = "https://etsi.me/search"
params = {
    "q": "What is Python programming",
    "format": "json",
    "categories": "general",
    "engines": "google,bing,duckduckgo",
    "pageno": 1
}

response = requests.get(searxng_url, params=params, timeout=10)
print(f"Status: {response.status_code}")
print(f"Results: {len(response.json().get('results', []))} found")
print(response.json().get('results', [])[:2])  # Show first 2 results