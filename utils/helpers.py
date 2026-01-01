import re, datetime, hashlib

def safe_name(s) -> str:
    """
    Convert any value into a safe string for filenames.
    Ensures lowercase, strips whitespace, replaces spaces with underscores.
    """
    if s is None:
        return "unnamed"
    # Convert non-string types to string first
    s = str(s)
    return s.lower().strip().replace(" ", "_")

def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]