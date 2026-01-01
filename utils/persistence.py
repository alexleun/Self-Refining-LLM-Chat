import os, json
from utils.helpers import safe_name

def save_evidence(project_id: str, docs: list) -> list:
    ev_dir = os.path.join(project_id, "evidence")
    os.makedirs(ev_dir, exist_ok=True)
    paths = []
    for d in docs:
        fname = f"{safe_name(d.get('title','doc'))}_{d['hash']}.json"
        path = os.path.join(ev_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        paths.append(path)
    return paths