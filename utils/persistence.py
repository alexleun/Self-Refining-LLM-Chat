import os
import re
import json

def sanitize_filename(name: str, max_len: int = 100) -> str:
    """
    Make a safe filename for Windows:
    - Remove invalid characters: \ / : * ? " < > |
    - Replace spaces with underscores
    - Trim to max_len
    """
    name = str(name)
    name = re.sub(r'[\\/:*?"<>|]', "_", name)   # replace invalid chars
    name = name.replace(" ", "_")
    return name[:max_len]

def save_evidence(project_id: str, sources: list) -> list:
    evidence_dir = os.path.join(project_id, "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    paths = []
    for src in sources:
        # Use URL or title as base name
        base = src.get("title") or src.get("url") or "evidence"
        safe_base = sanitize_filename(base)
        fname = f"{safe_base}_{src.get('hash','')}.json"
        path = os.path.join(evidence_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False, indent=2)
        paths.append(path)
    return paths