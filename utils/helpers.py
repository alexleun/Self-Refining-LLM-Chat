import re, datetime, hashlib

def safe_name(s: str, maxlen: int = 70) -> str:
    s = s.lower().strip().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s[:maxlen] if s else "untitled"

def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]