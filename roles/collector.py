import os, uuid, logging, requests
from utils.helpers import safe_name, file_hash
from roles.llm_interface import LLMInterface

class Collector:
    def __init__(self, tokens, llm: LLMInterface):
        self.tokens = tokens
        self.llm = llm

    def searx_search(self, query: str, limit: int = 8):
        params = {"q": query, "format": "json", "categories": "general", "language": "en"}
        try:
            resp = requests.get("http://localhost:8888/search", params=params, timeout=15)
            data = resp.json()
        except Exception as e:
            logging.error(f"SearXNG search failed: {e}")
            return []
        out = []
        for item in data.get("results", [])[:limit]:
            out.append({
                "source_id": str(uuid.uuid4()),
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "") or "",
                "date": item.get("publishedDate", ""),
                "engine": (item.get("engines") or ["general"])[0],
                "origin": "web-search",
            })
        return out

    def fetch_deep(self, url: str, max_chars: int = 4000) -> str:
        try:
            r = requests.get(url, timeout=60)
            return r.text[:max_chars]
        except Exception as e:
            logging.warning(f"Deep fetch failed: {url} :: {e}")
            return ""

    def ingest_local_files(self, root: str, patterns=(".md", ".txt")):
        docs = []
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if any(fn.lower().endswith(p) for p in patterns):
                    path = os.path.join(dirpath, fn)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                        docs.append({
                            "source_id": str(uuid.uuid4()),
                            "title": fn,
                            "url": path,
                            "snippet": text[:4000],
                            "date": "",
                            "engine": "local",
                            "origin": "local-file",
                        })
                    except Exception as e:
                        logging.warning(f"Failed to ingest local file: {path} :: {e}")
        return docs

    def compress_semantic(self, snippet: str, max_words: int) -> str:
        words = snippet.split()
        if len(words) <= max_words:
            return snippet
        prompt = (
            f"Rewrite the following text into ≤{max_words} words while preserving ALL factual details, "
            "actors, dates, and metrics. Do not omit key information.\n\n"
            f"{snippet}"
        )
        return self.llm.query(prompt, role="collector").strip()

    def collect(self, user_query: str, deep_visit=True, local_dir=None):
        results = self.searx_search(user_query, limit=8)
        for r in results:
            if deep_visit and r["url"]:
                text = self.fetch_deep(r["url"])
                if text:
                    r["snippet"] = text[:1200]
        if local_dir and os.path.isdir(local_dir):
            results.extend(self.ingest_local_files(local_dir))
        out = []
        for r in results:
            max_words = 200 if len(r["snippet"].split()) > 400 else 120
            r["compressed"] = self.compress_semantic(r["snippet"], max_words=max_words)
            r["hash"] = file_hash(r["compressed"])
            out.append(r)
        return out