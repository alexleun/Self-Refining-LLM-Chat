import requests

class SearxSearch:
    def __init__(self, base_url="http://localhost:8888"):
        """
        base_url: your SearxNG instance URL
        """
        self.base_url = base_url.rstrip("/")

    def search(self, query: str, limit: int = 8):
        """
        Perform a search via SearxNG API.
        Returns a list of dicts with at least 'url' and 'title'.
        """
        try:
            resp = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "categories": "general", "limit": limit},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                })
            return results
        except Exception as e:
            return [{"title": "Search error", "url": "", "snippet": str(e)}]

    def fetch_deep(self, url: str) -> str:
        """
        Fetch full page text for deeper snippet extraction.
        """
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            return f"Error fetching {url}: {e}"