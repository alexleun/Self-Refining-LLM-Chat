import re, datetime, hashlib

def safe_name(s) -> str:
    """
    Convert any value into a safe string for filenames.
    Ensures lowercase, strips whitespace, replaces spaces with underscores.
    """
    if s is None:
        return "unnamed"
    s = str(s)
    return s.lower().strip().replace(" ", "_")

def slugify_query(query: str, max_words: int = 5, max_len: int = 50) -> str:
    """
    Generate a human-readable slug from the query:
    - Take first `max_words` words
    - Remove non-alphanumeric characters
    - Join with underscores
    - Trim to `max_len` characters
    """
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())
    slug = "_".join(words[:max_words])
    return slug[:max_len]

def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]