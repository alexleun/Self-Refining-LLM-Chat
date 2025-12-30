# sketch_v3.py
# Self-Refining LLM Chat – Sketch v3
# Multi-role orchestration with EvidenceStore

import re, uuid, json, datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any

ROLE_DEFINITIONS = {
    "collector": """You are the Data Collector...""",
    "editor": """You are the Drafting Editor...""",
    "auditor": """You are the Auditor...""",
    "specialist": """You are the Specialist...""",
    "supervisor": """You are the Supervisor..."""
}

@dataclass
class Source:
    source_id: str
    title: str
    snippet: str
    url: str
    date: str
    relevance_score: float
    domain: str = "general"
    collector_notes: str = ""

class EvidenceStore:
    def __init__(self):
        self.store: Dict[str, List[Dict[str, Any]]] = {}

    def new_query(self, query: str) -> str:
        qid = str(uuid.uuid4())
        self.store[qid] = []
        return qid

    def add_evidence_pack(self, qid: str, round_num: int, sources: List[Dict[str, Any]], summary: Dict[str, List[str]]):
        pack = {
            "query_id": qid,
            "round": round_num,
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": sources,
            "summary": summary
        }
        self.store[qid].append(pack)

    def get_latest_pack(self, qid: str) -> Dict[str, Any]:
        return self.store[qid][-1] if qid in self.store and self.store[qid] else {}

    def get_all_sources(self, qid: str) -> List[Dict[str, Any]]:
        return [src for pack in self.store.get(qid, []) for src in pack["sources"]]

def parse_sources(raw_text: str) -> List[Dict[str, Any]]:
    sources = []
    chunks = re.split(r"\n\s*\n", raw_text.strip())
    for chunk in chunks:
        if not chunk.strip(): continue
        title = re.search(r"(Title|Conference|Source)[:\-]\s*(.+)", chunk, re.I)
        snippet = re.search(r"(Snippet|Summary|Note)[:\-]\s*(.+)", chunk, re.I)
        url = re.search(r"(URL|Link)[:\-]\s*(https?://\S+)", chunk, re.I)
        date = re.search(r"(Date)[:\-]\s*(.+)", chunk, re.I)
        relevance = re.search(r"(Relevance|Score)[:\-]\s*([\d\.]+)", chunk, re.I)
        sources.append({
            "source_id": str(uuid.uuid4()),
            "title": title.group(2).strip() if title else "Untitled",
            "snippet": snippet.group(2).strip() if snippet else chunk[:200],
            "url": url.group(2).strip() if url else "",
            "date": date.group(2).strip() if date else "",
            "relevance_score": float(relevance.group(2)) if relevance else 0.0,
            "domain": "general",
            "collector_notes": ""
        })
    return sources

def parse_review(review_text: str):
    try:
        obj = json.loads(review_text)
        return (
            int(obj.get("score", 0)),
            obj.get("strengths", []),
            obj.get("weaknesses", []),
            obj.get("improvements", []),
            obj.get("final_answer", "")
        )
    except Exception:
        return (0, [], [], [], "")

import requests

def query_llm(prompt: str) -> str:
    """
    Call LM Studio local server (OpenAI-compatible API).
    Make sure LM Studio is running with the REST API enabled.
    Default port is often 1234, adjust if needed.
    """
    resp = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json={
            "model": "your-local-model",   # e.g. "lmstudio-community/gpt-4-100k"
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000             # adjust per role
        }
    )
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def sketch_v3_loop(user_message: str, evidence_store: EvidenceStore, max_rounds: int = 6) -> str:
    qid = evidence_store.new_query(user_message)
    last_enriched = ""
    iteration_history = []

    for round_num in range(1, max_rounds+1):
        collector_prompt = f"{ROLE_DEFINITIONS['collector']}\nQuery: {user_message}"
        evidence_text = query_llm(collector_prompt)
        sources = parse_sources(evidence_text)
        evidence_store.add_evidence_pack(qid, round_num, sources, {"bullet_points": [], "contradictions": [], "gaps": []})

        latest_pack = evidence_store.get_latest_pack(qid)
        editor_prompt = f"{ROLE_DEFINITIONS['editor']}\nEvidence:\n{json.dumps(latest_pack, indent=2)}"
        draft = query_llm(editor_prompt)

        all_sources = evidence_store.get_all_sources(qid)
        auditor_prompt = f"{ROLE_DEFINITIONS['auditor']}\nDraft:\n{draft}\nSources:\n{json.dumps(all_sources, indent=2)}"
        audit_report = query_llm(auditor_prompt)

        specialist_prompt = f"{ROLE_DEFINITIONS['specialist']}\nDraft:\n{draft}\nAudit:\n{audit_report}"
        enriched_draft = query_llm(specialist_prompt)
        last_enriched = enriched_draft

        supervisor_prompt = f"{ROLE_DEFINITIONS['supervisor']}\nDraft:\n{enriched_draft}"
        review_text = query_llm(supervisor_prompt)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review_text)

        iteration_history.append({
            "round": round_num,
            "draft": enriched_draft,
            "audit": audit_report,
            "review": review_text,
            "score": score
        })

        if score >= 4 and not improvements:
            return enriched_draft

        user_message = f"{user_message}\nRefine by: {', '.join(improvements)}"

    return last_enriched or "No enriched draft produced."