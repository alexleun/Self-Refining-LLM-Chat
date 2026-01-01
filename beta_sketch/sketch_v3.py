import re, requests, json, logging, datetime, uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

logging.basicConfig(filename="session_v3.log", level=logging.INFO, format="%(message)s")

# ---------------------------
# Conversation State + Evidence
# ---------------------------

class ConversationState:
    def __init__(self):
        self.last_query = None
        self.last_draft = None
        self.last_feedback = None
        self.iteration_history = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_review_passed = False

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

@dataclass
class EvidencePack:
    query_id: str
    round: int
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    sources: List[Source] = field(default_factory=list)
    summary: Dict[str, List[str]] = field(default_factory=lambda: {
        "bullet_points": [], "contradictions": [], "gaps": []
    })

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

# ---------------------------
# Role Definitions
# ---------------------------

ROLE_DEFINITIONS = {
    "collector": """You are the Data Collector. Gather diverse sources and output structured evidence items:
Title, Snippet, URL, Date, Relevance. Separate items with blank lines.""",
    "editor": """You are the Drafting Editor. Turn evidence packs into a coherent, professional answer with headings and inline references.""",
    "auditor": """You are the Auditor. Check the draft against all sources. Identify contradictions, missing citations, weak evidence. Output a Gap Report.""",
    "specialist": """You are the Specialist. Add domain-specific insights, examples, trade-offs, and risks. Enrich the draft.""",
    "supervisor": """You are the Supervisor. Score the enriched draft from 1–5 against rubric: source integration, detail, synthesis, contradictions, tone. Output JSON with fields: score, strengths, weaknesses, improvements, final_answer."""
}

# ---------------------------
# Utilities
# ---------------------------

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

def safe_filename_from_query(query, suffix=".md"):
    fname = query.lower().strip().replace(" ", "_")
    fname = re.sub(r'[^a-z0-9_\-]', "", fname)
    if len(fname) > 50: fname = fname[:50]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{fname}_{timestamp}{suffix}"

def save_markdown(content, query, history=None):
    filename = safe_filename_from_query(query)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Final Generated Answer\n\n")
        f.write(content)
        if history:
            f.write("\n\n---\n\n# Iteration History\n")
            for h in history:
                f.write(f"\n## Round {h['round']} (Score {h['score']}/5)\n")
                f.write(f"\n**Draft:**\n\n{h['draft']}\n")
                f.write(f"\n**Audit:**\n\n{h['audit']}\n")
                f.write(f"\n**Review:**\n\n{h['review']}\n")
    print(f"Markdown file saved as {filename}")

# ---------------------------
# LM Studio Query
# ---------------------------

def query_llm(prompt: str) -> str:
    resp = requests.post(
        LM_STUDIO_URL,
        json={
            #"model": "openai/gpt-oss-20b",  # adjust to your LM Studio model
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 100000
        }
    )
    data = resp.json()
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
        elif "delta" in choice and "content" in choice["delta"]:
            return choice["delta"]["content"]
    return json.dumps(data, ensure_ascii=False, indent=2)

# ---------------------------
# Orchestration Loop
# ---------------------------

def sketch_v3_loop(user_message: str, state: ConversationState, evidence_store: EvidenceStore, max_rounds: int = 6) -> str:
    qid = evidence_store.new_query(user_message)
    last_enriched = ""

    for round_num in range(1, max_rounds+1):
        # Collector
        collector_prompt = f"{ROLE_DEFINITIONS['collector']}\nQuery: {user_message}"
        evidence_text = query_llm(collector_prompt)
        sources = parse_sources(evidence_text)
        evidence_store.add_evidence_pack(qid, round_num, sources, {"bullet_points": [], "contradictions": [], "gaps": []})

        # Editor
        latest_pack = evidence_store.get_latest_pack(qid)
        editor_prompt = f"{ROLE_DEFINITIONS['editor']}\nEvidence:\n{json.dumps(latest_pack, indent=2)}"
        draft = query_llm(editor_prompt)

        # Auditor
        all_sources = evidence_store.get_all_sources(qid)
        auditor_prompt = f"{ROLE_DEFINITIONS['auditor']}\nDraft:\n{draft}\nSources:\n{json.dumps(all_sources, indent=2)}"
        audit_report = query_llm(auditor_prompt)

        # Specialist
        specialist_prompt = f"{ROLE_DEFINITIONS['specialist']}\nDraft:\n{draft}\nAudit:\n{audit_report}"
        enriched_draft = query_llm(specialist_prompt)
        last_enriched = enriched_draft

        # Supervisor
        supervisor_prompt = f"{ROLE_DEFINITIONS['supervisor']}\nDraft:\n{enriched_draft}"
        review_text = query_llm(supervisor_prompt)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review_text)

        # --- Supervisor logging ---
        state.iteration_history.append({
            "round": round_num,
            "draft": enriched_draft,
            "audit": audit_report,
            "review": review_text,
            "score": score
        })

        # Decision logic
        if score >= 4 and not improvements:
            state.last_review_passed = True
            return enriched_draft
        else:
            # Refine query with supervisor improvements
            user_message = f"{user_message}\nRefine by: {', '.join(improvements)}"

    # Fallback: return last enriched draft
    state.last_review_passed = False
    return last_enriched or "No enriched draft produced."


# ---------------------------
# Main harness
# ---------------------------

if __name__ == "__main__":
    state = ConversationState()
    evidence_store = EvidenceStore()

    query = "Compare NeurIPS and ICML in terms of focus, scale, and industry relevance."
    answer = sketch_v3_loop(query, state, evidence_store, max_rounds=5)

    print("\n[FINAL ANSWER]")
    print(answer)
    print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")

    print("\n[ITERATION HISTORY]")
    for h in state.iteration_history:
        print(f"Round {h['round']} → Score {h['score']}/5")

    # Save Markdown with iteration history
    save_markdown(answer, query, history=state.iteration_history)