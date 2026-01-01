# sketch_v3_5.py
# Full scaffold with real Collector (SearXNG), deep visit, compression, scoring, logging

import re, requests, json, logging, datetime, uuid, time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

logging.basicConfig(
    filename="session_v3_5.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
JSONL_LOG = "session_v3_5_rounds.jsonl"

# ---------------------------
# Conversation State + Evidence
# ---------------------------

class ConversationState:
    def __init__(self):
        self.last_query: Optional[str] = None
        self.last_draft: Optional[str] = None
        self.last_feedback: Optional[str] = None
        self.iteration_history: List[Dict[str, Any]] = []
        self.last_review_passed: bool = False

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
        logging.info(f"New query initialized: {qid}")
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
        logging.info(f"Evidence pack added for qid={qid}, round={round_num}, sources={len(sources)}")

    def get_latest_pack(self, qid: str) -> Dict[str, Any]:
        return self.store[qid][-1] if qid in self.store and self.store[qid] else {}

    def get_all_sources(self, qid: str) -> List[Dict[str, Any]]:
        return [src for pack in self.store.get(qid, []) for src in pack["sources"]]

# ---------------------------
# Role Definitions
# ---------------------------

ROLE_TEMPERATURES = {
    "collector": 0.2,
    "editor": 0.5,
    "auditor": 0.2,
    "specialist": 0.7,
    "supervisor": 0.3,
    "fulfillment": 0.1,
    "critical": 0.9
}

ROLE_DEFINITIONS = {
    "editor": "You are the Drafting Editor. Write a clear Markdown report in requested language using evidence.",
    "auditor": "You are the Auditor. Check draft vs sources, flag contradictions, missing citations.",
    "specialist": "You are the Specialist. Add domain insights, trade-offs, risks, examples.",
    "supervisor": "You are the Supervisor. Score across dimensions. Return STRICT JSON:\n{\n  \"accuracy\":0,\n  \"coherence\":0,\n  \"completeness\":0,\n  \"creativity\":0,\n  \"format\":0,\n  \"overall\":0.0,\n  \"strengths\":[],\n  \"weaknesses\":[],\n  \"improvements\":[],\n  \"final_answer\":\"\"\n}",
    "fulfillment": "You are the Fulfillment Checker. Verify language, format, visuals, coverage. Return checklist.",
    "critical": "You are the Critical Thinker. Generate 2–3 probing questions."
}

# ---------------------------
# Token Counter
# ---------------------------

class TokenCounter:
    def __init__(self):
        self.role_usage = {}
        self.total = 0

    def add_usage(self, role: str, usage: Dict[str,int]):
        prompt = usage.get("prompt_tokens", 0)
        completion = usage.get("completion_tokens", 0)
        total = usage.get("total_tokens", 0)
        self.role_usage.setdefault(role, {"prompt":0,"completion":0,"total":0})
        self.role_usage[role]["prompt"] += prompt
        self.role_usage[role]["completion"] += completion
        self.role_usage[role]["total"] += total
        self.total += total

    def summary(self):
        lines = ["=== TOKEN SUMMARY ==="]
        for role, stats in self.role_usage.items():
            lines.append(f"{role}: prompt={stats['prompt']} completion={stats['completion']} total={stats['total']}")
        lines.append(f"TOTAL: {self.total}")
        return "\n".join(lines)

token_counter = TokenCounter()

# ---------------------------
# Collector with SearXNG
# ---------------------------

def searxng_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    url = "http://localhost:8888/search"
    params = {"q": query, "format": "json", "categories": "general", "language": "en"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        logging.error(f"SearXNG search failed: {e}")
        return []
    results = []
    for item in data.get("results", [])[:limit]:
        results.append({
            "source_id": str(uuid.uuid4()),
            "title": item.get("title", "Untitled"),
            "snippet": item.get("content", ""),
            "url": item.get("url", ""),
            "date": item.get("publishedDate", ""),
            "relevance_score": 0.5,
            "domain": item.get("engines", ["general"])[0],
            "collector_notes": "SearXNG result"
        })
    return results

def fetch_page_content(url: str, max_chars: int = 2000) -> str:
    try:
        resp = requests.get(url, timeout=10)
        return resp.text[:max_chars]
    except Exception as e:
        logging.warning(f"Failed to fetch {url}: {e}")
        return ""

def collector_stage(user_message: str, limit: int = 8) -> List[Dict[str, Any]]:
    results = searxng_search(user_message, limit=limit)
    for r in results:
        if r["url"]:
            page_text = fetch_page_content(r["url"])
            if page_text:
                r["snippet"] = page_text[:500]
                r["collector_notes"] = "Deep visited"
    return results

# ---------------------------
# Utilities
# ---------------------------

def parse_review(review_text: str):
    try:
        obj = json.loads(review_text)
        return (
            int(obj.get("accuracy", 0)),
            int(obj.get("coherence", 0)),
            int(obj.get("completeness", 0)),
            int(obj.get("creativity", 0)),
            int(obj.get("format", 0)),
            float(obj.get("overall", 0.0)),
            obj.get("strengths", []),
            obj.get("weaknesses", []),
            obj.get("improvements", []),
            obj.get("final_answer", "")
        )
    except Exception:
        logging.warning("Supervisor review not valid JSON.")
        return (0,0,0,0,0,0.0,[],[],[],"")

def safe_filename_from_query(query: str, suffix: str = ".md") -> str:
    fname = query.lower().strip().replace(" ", "_")
    fname = re.sub(r'[^a-z0-9_\-]', "", fname)
    if len(fname) > 50: fname = fname[:50]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{fname}_{timestamp}{suffix}"

def save_markdown(content: str, query: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    filename = safe_filename_from_query(query)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Final Generated Answer\n\n")
        f.write(content)
        if history:
            f.write("\n\n---\n\n# Iteration History\n")
            for h in history:
                f.write(
                    f"\n## Round {h['round']} Summary\n"
                    f"- Overall: {h['overall']}/10\n"
                    f"- Accuracy: {h['accuracy']} | Coherence: {h['coherence']} | "
                    f"Completeness: {h['completeness']} | Creativity: {h['creativity']} | "
                    f"Format: {h['format']}\n"
                    f"- Improvements suggested: {len(h['improvements'])}\n"
                    f"- Tokens used this round: {h.get('tokens_used',0)} | "
                    f"Cumulative: {h.get('tokens_total',0)}\n"
                    )
                f.write("\n**Draft:**\n\n" + h['draft'] + "\n")
                f.write("\n**Audit:**\n\n" + h['audit'] + "\n")
                f.write("\n**Supervisor Review (JSON):**\n\n" + h['review'] + "\n")
                f.write("\n**Fulfillment:**\n\n" + h.get('fulfillment','') + "\n")
                f.write("\n**Critical Questions:**\n\n" + h.get('critical','') + "\n")
    logging.info(f"Markdown file saved as {filename}")
    return filename

def log_jsonl(entry: Dict[str, Any]) -> None:
    with open(JSONL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ---------------------------
# LM Studio Query
# ---------------------------

class LLMConfig:
    def __init__(self, max_tokens: int = 2000, timeout: int = 60):
        self.max_tokens = max_tokens
        self.timeout = timeout

LLM_CONFIG = LLMConfig()

def query_llm(prompt: str, role: str, retries: int = 2, backoff: float = 0.75) -> str:
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": ROLE_TEMPERATURES.get(role, 0.7),
        "max_tokens": LLM_CONFIG.max_tokens,
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.post(LM_STUDIO_URL, json=payload, timeout=LLM_CONFIG.timeout)
            data = resp.json()
            if "usage" in data:
                token_counter.add_usage(role, data["usage"])
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"LLM request failed (attempt {attempt+1}/{retries+1}) for role={role}: {e}")
            time.sleep(backoff * (attempt + 1))
    return "[LLM Error] No response."

# ---------------------------
# Compression Upgrade
# ---------------------------

def compress_source_llm(source: Dict[str, Any]) -> Dict[str, Any]:
    words = source.get("snippet", "").split()
    max_words = 200 if len(words) > 400 else 120
    if len(words) <= max_words:
        return source
    prompt = (
        f"Rewrite the following snippet into ≤{max_words} words, "
        "preserving ALL factual details, actors, dates, and metrics. "
        "Do not omit key information.\n\n"
        f"{source.get('snippet','')}"
    )
    compressed = query_llm(prompt, role="collector")
    source["snippet"] = compressed.strip()
    return source

# ---------------------------
# Orchestration Loop
# ---------------------------

def sketch_v3_5_loop(user_message: str, state: ConversationState,
                     evidence_store: EvidenceStore, max_rounds: int = 6,
                     language_hint: str = "繁體中文") -> str:
    qid = evidence_store.new_query(user_message)
    last_enriched = ""
    state.last_query = user_message
    prev_total = 0

    for round_num in range(1, max_rounds + 1):
        logging.info(f"=== Round {round_num} start ===")

        # Collector
        sources = collector_stage(user_message, limit=8)
        sources = [compress_source_llm(s) for s in sources]
        evidence_store.add_evidence_pack(qid, round_num, sources,
                                         {"bullet_points": [], "contradictions": [], "gaps": []})

        # Editor
        latest_pack = evidence_store.get_latest_pack(qid)
        editor_prompt = f"{ROLE_DEFINITIONS['editor']}\nWrite in {language_hint}.\nEvidence:\n{json.dumps(latest_pack, ensure_ascii=False, indent=2)}"
        draft = query_llm(editor_prompt, "editor")

        # Auditor
        all_sources = evidence_store.get_all_sources(qid)
        auditor_prompt = f"{ROLE_DEFINITIONS['auditor']}\nDraft:\n{draft}\nSources:\n{json.dumps(all_sources, ensure_ascii=False, indent=2)}"
        audit_report = query_llm(auditor_prompt, "auditor")

        # Specialist
        specialist_prompt = f"{ROLE_DEFINITIONS['specialist']}\nDraft:\n{draft}\nAudit:\n{audit_report}"
        enriched_draft = query_llm(specialist_prompt, "specialist")
        last_enriched = enriched_draft
        state.last_draft = enriched_draft

        # Supervisor
        supervisor_prompt = f"{ROLE_DEFINITIONS['supervisor']}\nDraft:\n{enriched_draft}"
        review_text = query_llm(supervisor_prompt, "supervisor")
        accuracy, coherence, completeness, creativity, format_score, overall, strengths, weaknesses, improvements, final_answer = parse_review(review_text)

        # Fulfillment Checker
        fulfillment_prompt = f"{ROLE_DEFINITIONS['fulfillment']}\nUser Query:\n{user_message}\nDraft:\n{enriched_draft}"
        fulfillment_report = query_llm(fulfillment_prompt, "fulfillment")

        # Critical Thinker
        critical_prompt = f"{ROLE_DEFINITIONS['critical']}\nDraft:\n{enriched_draft}"
        critical_questions = query_llm(critical_prompt, "critical")

        # Token summary per round
        round_tokens = token_counter.total - prev_total
        logging.info(
            f"[ROUND {round_num}] overall={overall}/10 acc={accuracy} coh={coherence} "
            f"comp={completeness} cre={creativity} fmt={format_score} "
            f"improvements={len(improvements)}"
        )
        logging.info(f"[ROUND {round_num}] tokens_used={round_tokens} total={token_counter.total}")
        prev_total = token_counter.total

        # Build round entry
        round_entry = {
            "qid": qid,
            "round": round_num,
            "draft": enriched_draft,
            "audit": audit_report,
            "review": review_text,
            "accuracy": accuracy,
            "coherence": coherence,
            "completeness": completeness,
            "creativity": creativity,
            "format": format_score,
            "overall": overall,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": improvements,
            "fulfillment": fulfillment_report,
            "critical": critical_questions,
            "tokens_used": round_tokens,
            "tokens_total": token_counter.total
        }
        state.iteration_history.append(round_entry)
        log_jsonl(round_entry)

        # Decision
        if overall >= 8.0 and not improvements:
            state.last_review_passed = True
            return enriched_draft
        else:
            user_message = f"{state.last_query}\nRefine by: {', '.join(improvements[:5])}"

    state.last_review_passed = False
    return last_enriched or "No enriched draft produced."

# ---------------------------
# Main harness
# ---------------------------

if __name__ == "__main__":
    state = ConversationState()
    evidence_store = EvidenceStore()

    query = "深度研究：請用繁體中文撰寫報告，並生成圖表或圖片輔助理解。主題來源：https://www.jdsupra.com/legalnews/governing-the-ungovernable-corporate-1075132/"
    answer = sketch_v3_5_loop(query, state, evidence_store, max_rounds=3)

    print("\n[FINAL ANSWER]")
    print(answer)
    print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")

    print("\n[ITERATION HISTORY]")
    for h in state.iteration_history:
        print(f"Round {h['round']} → Overall {h['overall']}/10")
        print("Fulfillment:", h.get("fulfillment", ""))
        print("Critical Questions:", h.get("critical", ""))

    save_markdown(answer, query, history=state.iteration_history)
    print("\n" + token_counter.summary())