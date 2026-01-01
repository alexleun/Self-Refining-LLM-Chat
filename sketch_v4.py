# sketch_v4.py
# Run: python sketch_v4.py

import os, re, json, time, uuid, hashlib, logging, datetime, requests
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"  # model not specified; LM Studio decides
SEARX_URL = "http://localhost:8888/search"

logging.basicConfig(filename="sketch_v4.log", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# Utilities
# ---------------------------

def safe_name(s: str, maxlen: int = 70) -> str:
    s = s.lower().strip().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s[:maxlen] if s else "untitled"

def now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

@dataclass
class TokenCounter:
    role_usage: Dict[str, Dict[str,int]] = field(default_factory=dict)
    total: int = 0
    def add(self, role: str, usage: Dict[str,int]):
        self.role_usage.setdefault(role, {"prompt":0,"completion":0,"total":0})
        self.role_usage[role]["prompt"] += usage.get("prompt_tokens", 0)
        self.role_usage[role]["completion"] += usage.get("completion_tokens", 0)
        t = usage.get("total_tokens", 0)
        self.role_usage[role]["total"] += t
        self.total += t

ROLE_TEMPS = {
    "planner": 0.4, "decomposer": 0.4, "collector": 0.2, "editor": 0.5,
    "auditor": 0.2, "specialist": 0.7, "supervisor": 0.3, "fulfillment": 0.1, "critical": 0.9
}

class LLMConfig:
    def __init__(self, max_tokens: int = 2000, timeout: int = 60):
        self.max_tokens = max_tokens
        self.timeout = timeout

LLM_CFG = LLMConfig()

def query_llm(prompt: str, role: str, tokens: TokenCounter, retries: int = 2, backoff: float = 0.75) -> str:
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": ROLE_TEMPS.get(role, 0.7),
        "max_tokens": LLM_CFG.max_tokens,
    }
    for attempt in range(retries+1):
        try:
            r = requests.post(LM_STUDIO_URL, json=payload, timeout=LLM_CFG.timeout)
            data = r.json()
            if "usage" in data: tokens.add(role, data["usage"])
            if "choices" in data and data["choices"]:
                m = data["choices"][0].get("message", {})
                if m and "content" in m: return m["content"]
                d = data["choices"][0].get("delta", {})
                if "content" in d: return d["content"]
            return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            logging.error(f"LLM error role={role} attempt={attempt+1}: {e}")
            time.sleep(backoff * (attempt+1))
    return "[LLM Error]"

# ---------------------------
# Agentic RAG: collection and persistence
# ---------------------------

def searx_search(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    params = {"q": query, "format": "json", "categories": "general", "language": "en"}
    try:
        resp = requests.get(SEARX_URL, params=params, timeout=15)
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

def fetch_deep(url: str, max_chars: int = 4000) -> str:
    try:
        r = requests.get(url, timeout=10)
        return r.text[:max_chars]
    except Exception as e:
        logging.warning(f"Deep fetch failed: {url} :: {e}")
        return ""

def ingest_local_files(root: str, patterns: Tuple[str, ...] = (".md", ".txt")) -> List[Dict[str, Any]]:
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

def compress_semantic(snippet: str, role: str, tokens: TokenCounter, max_words: int) -> str:
    words = snippet.split()
    if len(words) <= max_words: return snippet
    prompt = (
        f"Rewrite the following text into ≤{max_words} words while preserving ALL factual details, "
        "actors, dates, and metrics. Do not omit key information.\n\n"
        f"{snippet}"
    )
    return query_llm(prompt, role=role, tokens=tokens).strip()

def collector(user_query: str, tokens: TokenCounter, deep_visit: bool = True,
              local_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    # Web search + deep visit
    results = searx_search(user_query, limit=8)
    for r in results:
        if deep_visit and r["url"]:
            text = fetch_deep(r["url"])
            if text: r["snippet"] = text[:1200]

    # Local ingestion
    if local_dir and os.path.isdir(local_dir):
        results.extend(ingest_local_files(local_dir, patterns=(".md", ".txt")))

    # Adaptive compression
    out = []
    for r in results:
        max_words = 200 if len(r["snippet"].split()) > 400 else 120
        r["compressed"] = compress_semantic(r["snippet"], role="collector", tokens=tokens, max_words=max_words)
        r["hash"] = file_hash(r["compressed"])
        out.append(r)
    return out

def save_evidence(project_id: str, docs: List[Dict[str, Any]]) -> List[str]:
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

# ---------------------------
# Planning and decomposition
# ---------------------------

def planner(user_query: str, tokens: TokenCounter) -> Dict[str, Any]:
    prompt = (
        "You are the Planner. Create a concise JSON plan with:\n"
        "- goals: [..]\n- milestones: [{id, name, deliverables, target_date}],\n"
        "- risks: [..]\n- success_criteria: [..]\n\nQuery:\n" + user_query + "\nReturn STRICT JSON."
    )
    raw = query_llm(prompt, role="planner", tokens=tokens)
    try:
        return json.loads(raw)
    except Exception:
        return {"goals": [], "milestones": [], "risks": [], "success_criteria": [], "raw": raw}

def decomposer(plan: Dict[str, Any], tokens: TokenCounter) -> Dict[str, Any]:
    prompt = (
        "You are the Decomposer. Given this plan JSON, produce a task graph JSON with:\n"
        "sections: [{id, title, query, deliverables}],\n"
        "dependencies: [{from, to}],\n"
        "metrics: [{name, how_to_measure}].\nReturn STRICT JSON.\n\nPlan:\n" + json.dumps(plan, ensure_ascii=False)
    )
    raw = query_llm(prompt, role="decomposer", tokens=tokens)
    try:
        return json.loads(raw)
    except Exception:
        return {"sections": [], "dependencies": [], "metrics": [], "raw": raw}

# ---------------------------
# Sectional drafting and audits
# ---------------------------

def editor_section(section: Dict[str, Any], evidence: List[Dict[str, Any]], language_hint: str, tokens: TokenCounter) -> str:
    prompt = (
        "You are the Drafting Editor.\n"
        f"Write in {language_hint}.\n"
        "Produce a Markdown section with heading, short paragraphs, bullets, and cite sources inline by Title or URL.\n\n"
        "Section:\n" + json.dumps(section, ensure_ascii=False) + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
    )
    return query_llm(prompt, role="editor", tokens=tokens)

def auditor_section(draft: str, evidence: List[Dict[str, Any]], tokens: TokenCounter) -> str:
    prompt = (
        "You are the Auditor.\nCheck the draft against the evidence.\n"
        "Return concise bullets: contradictions, unsupported claims, missing citations, and specific fixes.\n\n"
        "Draft:\n" + draft + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
    )
    return query_llm(prompt, role="auditor", tokens=tokens)

def specialist_enrich(draft: str, audit: str, tokens: TokenCounter) -> str:
    prompt = (
        "You are the Specialist.\nEnrich the draft with domain insights, trade-offs, risks, and examples.\n"
        "Add an 'Insights & Scenarios' subsection. Do not remove citations.\n\nDraft:\n" + draft + "\n\nAudit:\n" + audit
    )
    return query_llm(prompt, role="specialist", tokens=tokens)

def supervisor_score(draft: str, tokens: TokenCounter) -> Dict[str, Any]:
    prompt = (
        "You are the Supervisor.\nScore the draft across dimensions and return STRICT JSON only:\n"
        "{ \"accuracy\":0, \"coherence\":0, \"completeness\":0, \"creativity\":0, \"format\":0, "
        "\"overall\":0.0, \"strengths\":[], \"weaknesses\":[], \"improvements\":[], \"final_answer\":\"\" }.\n\n"
        "Draft:\n" + draft
    )
    raw = query_llm(prompt, role="supervisor", tokens=tokens)
    try:
        return json.loads(raw)
    except Exception:
        return {"accuracy":0,"coherence":0,"completeness":0,"creativity":0,"format":0,"overall":0.0,"strengths":[],"weaknesses":[],"improvements":[],"final_answer":raw}

def fulfillment_check(user_query: str, draft: str, tokens: TokenCounter) -> str:
    prompt = (
        "You are the Fulfillment Checker.\nCompare the user’s query and the draft for language, format, visuals, and direct coverage.\n"
        "Return a short checklist with Pass/Fail and 1–2 lines of rationale.\n\n"
        "User Query:\n" + user_query + "\n\nDraft:\n" + draft
    )
    return query_llm(prompt, role="fulfillment", tokens=tokens)

def critical_questions(draft: str, tokens: TokenCounter) -> str:
    prompt = (
        "You are the Critical Thinker.\nGenerate 2–3 probing questions that challenge assumptions and broaden angles.\n"
        "Return questions only.\n\nDraft:\n" + draft
    )
    return query_llm(prompt, role="critical", tokens=tokens)

# ---------------------------
# Orchestration (milestone + sectional)
# ---------------------------

def sketch_v4_run(user_query: str, language_hint: str = "繁體中文", max_rounds: int = 3,
                  local_evidence_dir: Optional[str] = None) -> Dict[str, Any]:
    project_id = safe_name(user_query) + "_" + now_ts()
    os.makedirs(project_id, exist_ok=True)
    os.makedirs(os.path.join(project_id, "evidence"), exist_ok=True)
    os.makedirs(os.path.join(project_id, "sections"), exist_ok=True)

    tokens = TokenCounter()
    plan = planner(user_query, tokens)
    tasks = decomposer(plan, tokens)

    with open(os.path.join(project_id, "plan.json"), "w", encoding="utf-8") as f: json.dump(plan, f, ensure_ascii=False, indent=2)
    with open(os.path.join(project_id, "tasks.json"), "w", encoding="utf-8") as f: json.dump(tasks, f, ensure_ascii=False, indent=2)

    iteration_history = []
    cumulative_sources: List[Dict[str, Any]] = []
    manifest = {"project_id": project_id, "artifacts": []}

    prev_total = 0
    sections = tasks.get("sections", []) or [{"id":"sec-1","title":"Overview","query":user_query,"deliverables":["report"]}]

    for round_num in range(1, max_rounds+1):
        logging.info(f"=== Round {round_num} start ===")

        # Collect evidence (web + local) and persist
        fresh_sources = collector(user_query, tokens, deep_visit=True, local_dir=local_evidence_dir)
        evidence_paths = save_evidence(project_id, fresh_sources)
        manifest["artifacts"].extend([{"type":"evidence","path":p} for p in evidence_paths])

        # Pool evidence (deduplicate by URL/hash)
        cumulative_sources.extend(fresh_sources)
        dedup = []; seen = set()
        for s in cumulative_sources:
            key = (s.get("url","").strip().lower(), s.get("hash",""))
            if key not in seen:
                seen.add(key); dedup.append(s)
        cumulative_sources = dedup

        section_outputs = []
        for sec in sections:
            sec_dir = os.path.join(project_id, "sections", safe_name(sec.get("id", sec.get("title","sec"))))
            os.makedirs(sec_dir, exist_ok=True)

            ev = fresh_sources  # current round evidence; could mix with cumulative if desired
            draft = editor_section(sec, ev, language_hint, tokens)
            audit = auditor_section(draft, ev, tokens)
            enriched = specialist_enrich(draft, audit, tokens)
            score = supervisor_score(enriched, tokens)
            fulfill = fulfillment_check(user_query, enriched, tokens)
            critical = critical_questions(enriched, tokens)

            with open(os.path.join(sec_dir, f"draft_round{round_num}.md"), "w", encoding="utf-8") as f: f.write(enriched)
            with open(os.path.join(sec_dir, f"audit_round{round_num}.md"), "w", encoding="utf-8") as f: f.write(audit)
            with open(os.path.join(sec_dir, f"score_round{round_num}.json"), "w", encoding="utf-8") as f: json.dump(score, f, ensure_ascii=False, indent=2)
            with open(os.path.join(sec_dir, f"fulfillment_round{round_num}.md"), "w", encoding="utf-8") as f: f.write(fulfill)
            with open(os.path.join(sec_dir, f"critical_round{round_num}.md"), "w", encoding="utf-8") as f: f.write(critical)

            section_outputs.append({"section": sec, "draft": enriched, "audit": audit, "score": score, "fulfillment": fulfill, "critical": critical})

        # Round summary logs
        round_tokens = tokens.total - prev_total
        avg_overall = sum(o["score"].get("overall", 0.0) for o in section_outputs) / max(1, len(section_outputs))
        total_improvements = sum(len(o["score"].get("improvements", [])) for o in section_outputs)
        logging.info(f"[ROUND {round_num}] sections={len(section_outputs)} avg_overall={avg_overall:.2f} improvements={total_improvements}")
        logging.info(f"[ROUND {round_num}] tokens_used={round_tokens} total={tokens.total}")
        prev_total = tokens.total

        iteration_history.append({
            "round": round_num,
            "avg_overall": avg_overall,
            "tokens_used": round_tokens,
            "tokens_total": tokens.total,
            "sections": section_outputs
        })

        # Simple stop condition
        if avg_overall >= 8.0 and total_improvements == 0:
            break

    # Integrate sections into final report
    final_md = ["# 最終報告",""]
    for o in iteration_history[-1]["sections"]:
        title = o["section"].get("title", "Section")
        final_md.append(f"## {title}\n")
        final_md.append(o["draft"])
        final_md.append("")

    final_text = "\n".join(final_md)
    with open(os.path.join(project_id, "final_report.md"), "w", encoding="utf-8") as f: f.write(final_text)
    with open(os.path.join(project_id, "history.json"), "w", encoding="utf-8") as f: json.dump(iteration_history, f, ensure_ascii=False, indent=2)
    with open(os.path.join(project_id, "evidence_pool.json"), "w", encoding="utf-8") as f: json.dump(cumulative_sources, f, ensure_ascii=False, indent=2)
    with open(os.path.join(project_id, "manifest.json"), "w", encoding="utf-8") as f: json.dump(manifest, f, ensure_ascii=False, indent=2)

    return {
        "project_id": project_id,
        "final_report_path": os.path.join(project_id, "final_report.md"),
        "iteration_history": iteration_history,
        "token_summary": {"total": tokens.total, "by_role": tokens.role_usage}
    }

# ---------------------------
# CLI harness
# ---------------------------

if __name__ == "__main__":
    query = "深度研究：請用繁體中文撰寫報告，並生成圖表或圖片輔助理解。主題來源：https://www.jdsupra.com/legalnews/governing-the-ungovernable-corporate-1075132/"
    result = sketch_v4_run(query, language_hint="繁體中文", max_rounds=3, local_evidence_dir=None)
    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])