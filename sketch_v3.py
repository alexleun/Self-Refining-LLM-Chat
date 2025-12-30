# sketch_v3.py
# Sketch v3 – Multi-Role Orchestration with EvidenceStore (Test Scaffold)
# Run: python sketch_v3.py "Your query here"

import re
import os
import sys
import uuid
import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any

# ---------------------------
# Role definitions (prompts)
# ---------------------------

ROLE_DEFINITIONS = {
    "collector": """
You are the Data Collector.
- Search and summarize diverse sources.
- Provide structured evidence snippets with: Title, Snippet, URL, Date, Relevance.
- Do not write narrative; only evidence items separated by blank lines.
""",
    "editor": """
You are the Drafting Editor.
- Turn evidence packs into a coherent, professional answer.
- Use headings, tables, and inline references (e.g., [Title]) where appropriate.
- Do not fabricate data; only synthesize from evidence given.
""",
    "auditor": """
You are the Auditor.
- Check the draft against all sources.
- Identify contradictions, missing citations, weak or outdated evidence.
- Output a concise Gap Report with bullets: Missing, Contradictions, Uncertainties.
""",
    "specialist": """
You are the Specialist.
- Add domain-specific insights and practical, actionable guidance.
- Provide examples, trade-offs, and risks relevant to the query context.
- Enrich the draft; do not change citations or invent sources.
""",
    "supervisor": """
You are the Supervisor.
- Score the enriched draft from 1–5 against the rubric:
  source integration, contextual detail, synthesis, contradictions, professional tone.
- Output a JSON object with fields: score (int), strengths (list), weaknesses (list),
  improvements (list), final_answer (str or empty).
"""
}

# ---------------------------
# Data structures
# ---------------------------

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
        "bullet_points": [],
        "contradictions": [],
        "gaps": []
    })


class EvidenceStore:
    """Manages evidence packs across rounds for a given query."""
    def __init__(self):
        self.store: Dict[str, List[Dict[str, Any]]] = {}  # query_id → list of packs

    def new_query(self, query: str) -> str:
        query_id = str(uuid.uuid4())
        self.store[query_id] = []
        return query_id

    def add_evidence_pack(self, query_id: str, round_num: int, sources: List[Dict[str, Any]], summary: Dict[str, List[str]]):
        pack = {
            "query_id": query_id,
            "round": round_num,
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": sources,
            "summary": summary
        }
        self.store[query_id].append(pack)

    def get_latest_pack(self, query_id: str) -> Dict[str, Any]:
        if query_id not in self.store or not self.store[query_id]:
            return {}
        return self.store[query_id][-1]

    def get_all_sources(self, query_id: str) -> List[Dict[str, Any]]:
        if query_id not in self.store:
            return []
        return [src for pack in self.store[query_id] for src in pack["sources"]]

    def get_summary_history(self, query_id: str) -> List[Dict[str, List[str]]]:
        if query_id not in self.store:
            return []
        return [pack["summary"] for pack in self.store[query_id]]

# ---------------------------
# Utilities
# ---------------------------

def parse_sources(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse the Collector's raw text into a list of source dicts.
    Expected fields per chunk:
      Title: ...
      Snippet: ...
      URL: ...
      Date: ...
      Relevance: ...
    """
    sources: List[Dict[str, Any]] = []
    # Split chunks by double newline; tolerate bullets.
    chunks = re.split(r"\n\s*\n", raw_text.strip())

    for chunk in chunks:
        if not chunk.strip():
            continue
        title_match = re.search(r"(Title|Conference|Source)[:\-]\s*(.+)", chunk, re.I)
        snippet_match = re.search(r"(Snippet|Summary|Note)[:\-]\s*(.+)", chunk, re.I)
        url_match = re.search(r"(URL|Link)[:\-]\s*(https?://\S+)", chunk, re.I)
        date_match = re.search(r"(Date)[:\-]\s*(.+)", chunk, re.I)
        relevance_match = re.search(r"(Relevance|Score)[:\-]\s*([\d\.]+)", chunk, re.I)

        source = {
            "source_id": str(uuid.uuid4()),
            "title": title_match.group(2).strip() if title_match else "Untitled",
            "snippet": snippet_match.group(2).strip() if snippet_match else chunk[:200].strip(),
            "url": url_match.group(2).strip() if url_match else "",
            "date": date_match.group(2).strip() if date_match else "",
            "relevance_score": float(relevance_match.group(2)) if relevance_match else 0.0,
            "domain": "general",
            "collector_notes": ""
        }
        sources.append(source)
    return sources


def safe_filename_from_query(query: str, suffix: str = ".md") -> str:
    fname = query.lower().strip().replace(" ", "_")
    fname = re.sub(r'[^a-z0-9_\-]', "", fname)
    if len(fname) > 80:
        fname = fname[:80]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{fname}_{timestamp}{suffix}"


def save_markdown(content: str, query: str, history: List[Dict[str, Any]] = None, filename: str = None) -> str:
    if not filename:
        filename = safe_filename_from_query(query)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Final Generated Answer\n\n")
        f.write(content)
        if history:
            f.write("\n\n---\n\n# Iteration History\n")
            for h in history:
                f.write(f"\n## Round {h.get('round')} (Score {h.get('score')}/5)\n")
                f.write("\n**Draft:**\n\n")
                f.write(h.get("draft", "") + "\n")
                f.write("\n**Audit:**\n\n")
                f.write(h.get("audit", "") + "\n")
                f.write("\n**Review:**\n\n")
                f.write(h.get("review", "") + "\n")
    return filename


# ---------------------------
# Mock LLM for local testing
# ---------------------------

def query_llm(prompt: str, state: Dict[str, Any]) -> Tuple[str, int, float]:
    """
    Minimal mock LLM:
    - For collector: returns 3 structured sources tied to the query.
    - For editor: synthesizes a short narrative with inline refs.
    - For auditor: flags simple gaps and contradictions.
    - For specialist: adds pragmatic, domain tips.
    - For supervisor: outputs a JSON review with score and improvements.
    """
    text = prompt.lower()

    if "you are the data collector" in text:
        q = state.get("query", "query")
        return (f"""Title: Source A for {q}
Snippet: Overview with dates and stakeholders relevant to {q}.
URL: https://example.com/a
Date: 2025-05-01
Relevance: 0.90

Title: Source B for {q}
Snippet: Practical outcomes, conversion rates, and costs related to {q}.
URL: https://example.com/b
Date: 2025-06-15
Relevance: 0.85

Title: Source C for {q}
Snippet: Contrasting viewpoints and uncertainties surrounding {q}.
URL: https://example.com/c
Date: 2025-07-20
Relevance: 0.80
""", 250, 0.001)

    if "you are the drafting editor" in text:
        # Extract evidence blob (rough)
        return ("""## Synthesis

- The evidence indicates key stakeholders, dates, and costs [Source A][Source B].
- Practical outcomes include measurable conversion and follow-up timing [Source B].
- Noted uncertainties and trade-offs highlight regional or format considerations [Source C].

### Actionable next steps
- Define objective and prepare a 2-minute narrative with metrics.
- Book early; mix virtual workshops with targeted in-person demos.
- Follow up within 48 hours with quantified asks and next steps.
""", 400, 0.002)

    if "you are the auditor" in text:
        return ("""Gap Report
- Missing: explicit inline citations to URLs; quantify ranges (cost, conversion).
- Contradictions: none detected; but uncertainty not tied to specific sources.
- Uncertainties: hybrid vs in-person ROI; regional variance in investor density.
""", 200, 0.001)

    if "you are the specialist" in text:
        return ("""## Specialist insights

- Trade-offs: in-person demos improve conversion when hardware or physical UX matters; otherwise virtual suffices.
- Risks: over-attendance (>3 events/yr) yields diminishing returns; prioritize fit over visibility.
- Examples: pair a flagship research venue with a domain pilot event; track ROI with a simple post-event metric sheet.
""", 250, 0.001)

    if "you are the supervisor" in text:
        review = {
            "score": 4,
            "strengths": [
                "Clear structure and actionable steps",
                "Evidence touches stakeholders, outcomes, uncertainties"
            ],
            "weaknesses": [
                "Inline citations not fully explicit",
                "Quantitative ranges could be tighter"
            ],
            "improvements": [
                "Add explicit citations to each claim",
                "Quantify costs and conversion with ranges"
            ],
            "final_answer": ""
        }
        return (json.dumps(review, indent=2), 120, 0.001)

    # Default echo
    return ("", 1, 0.0)


def parse_review(review_text: str) -> Tuple[int, List[str], List[str], List[str], str]:
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

# ---------------------------
# Orchestration loop (v3)
# ---------------------------

def sketch_v3_loop(user_message: str, state: Dict[str, Any], evidence_store: EvidenceStore, max_rounds: int = 6) -> str:
    query_id = evidence_store.new_query(user_message)
    state["query"] = user_message
    iteration_history: List[Dict[str, Any]] = []
    last_enriched = ""

    for round_num in range(1, max_rounds + 1):
        # 1. Collector
        collector_prompt = f"{ROLE_DEFINITIONS['collector']}\nQuery: {user_message}"
        evidence_text, _, _ = query_llm(collector_prompt, state)
        sources = parse_sources(evidence_text)
        summary = {"bullet_points": [], "contradictions": [], "gaps": []}
        evidence_store.add_evidence_pack(query_id, round_num, sources, summary)

        # 2. Editor
        latest_pack = evidence_store.get_latest_pack(query_id)
        editor_prompt = f"{ROLE_DEFINITIONS['editor']}\nEvidence:\n{json.dumps(latest_pack, indent=2)}"
        draft, _, _ = query_llm(editor_prompt, state)

        # 3. Auditor
        all_sources = evidence_store.get_all_sources(query_id)
        auditor_prompt = f"{ROLE_DEFINITIONS['auditor']}\nDraft:\n{draft}\nSources:\n{json.dumps(all_sources, indent=2)}"
        audit_report, _, _ = query_llm(auditor_prompt, state)
        latest_pack["summary"]["contradictions"].append(audit_report)

        # 4. Specialist
        specialist_prompt = f"{ROLE_DEFINITIONS['specialist']}\nDraft:\n{draft}\nAudit:\n{audit_report}"
        enriched_draft, _, _ = query_llm(specialist_prompt, state)
        last_enriched = enriched_draft

        # 5. Supervisor
        supervisor_prompt = f"{ROLE_DEFINITIONS['supervisor']}\nDraft:\n{enriched_draft}"
        review_text, _, _ = query_llm(supervisor_prompt, state)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review_text)

        iteration_history.append({
            "round": round_num,
            "draft": enriched_draft,
            "audit": audit_report,
            "review": review_text,
            "score": score
        })

        # Decision
        if score >= 4 and not improvements:
            return enriched_draft
        else:
            # Refine query by feeding improvements (simple concatenation for test)
            user_message = f"{state['query']}\nRefine by: {', '.join(improvements)}"

    return last_enriched or "No enriched draft produced."

# ---------------------------
# Main (test harness)
# ---------------------------

def main():
    query = "Which AI conferences in 2025 should a startup founder attend, and why?"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print(f"[Query] {query}\n")

    evidence_store = EvidenceStore()
    state: Dict[str, Any] = {}

    final_answer = sketch_v3_loop(query, state, evidence_store, max_rounds=6)
    print("=== FINAL ANSWER (Preview) ===\n")
    print(final_answer)

    # Save markdown with full iteration history
    filename = save_markdown(final_answer, query, history=state.get("iteration_history", []))
    print(f"\n[Saved] {filename}")

    # Optional: simple inspection
    # Extract and print source titles
    # (Using internal store for quick visibility)
    # Note: Iteration history is tracked locally in this scaffold; augment as needed.
    print("\n=== SOURCES ===")
    # Use the latest query_id (last key)
    if evidence_store.store:
        # Get the last query_id inserted
        last_query_id = list(evidence_store.store.keys())[-1]
        for src in evidence_store.get_all_sources(last_query_id):
            print(f"- {src.get('title')} ({src.get('url')}) [Relevance: {src.get('relevance_score')}]")

if __name__ == "__main__":
    main()