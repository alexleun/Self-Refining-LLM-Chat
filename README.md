
# Self-Refining LLM Chat – Sketch v3

## Overview
Sketch v3 is the third iteration of the **Self-Refining LLM Chat System**, designed to overcome the stagnation observed in v2’s linear supervisor loop.  
This version introduces **multi-role orchestration** and a persistent **EvidenceStore** to ensure every round injects fresh sources, domain insights, and rigorous auditing.

---

## ✨ Features

- **Multi-Role Pipeline**
  - **Collector** – gathers and structures search results into evidence packs.
  - **Editor** – drafts coherent narrative answers with citations.
  - **Auditor** – checks drafts against evidence, flags contradictions and gaps.
  - **Specialist** – injects domain-specific insights and examples.
  - **Supervisor** – scores drafts, enforces rubric, and decides continuation.

- **EvidenceStore**
  - Persistent storage of search results across rounds.
  - Structured schema with sources, summaries, contradictions, and gaps.
  - Accessible to all roles for traceability and auditability.

- **Dynamic Refinement**
  - Supervisor feedback drives query refinement.
  - Collector refreshes search with new keywords each round.
  - Prevents stagnation by continuously injecting new evidence.

- **Audit Trail**
  - Iteration history logs drafts, audits, reviews, and scores.
  - Markdown export includes final answer + role contributions.

- **Dashboard Integration**
  - Charts for score progression, token usage, and role impact.
  - Legends placed outside chart area for clarity.

---

## 🧩 Architecture

```
User Query
   ↓
Collector → Evidence Pack → EvidenceStore
   ↓
Editor → Draft
   ↓
Auditor → Gap Report
   ↓
Specialist → Enriched Draft
   ↓
Supervisor → Score + Feedback
   ↓
Loop Control → Refine Query → Collector refresh
```

---

## 📂 EvidenceStore Schema

```json
{
  "query_id": "uuid",
  "round": 1,
  "timestamp": "2025-12-30T15:39:00Z",
  "sources": [
    {
      "source_id": "src_001",
      "title": "NeurIPS 2025 Program Overview",
      "snippet": "Startup & Innovation track...",
      "url": "https://neurips.cc/Conferences/2025",
      "date": "2025-12-01",
      "relevance_score": 0.92,
      "domain": "conference",
      "collector_notes": "High VC density."
    }
  ],
  "summary": {
    "bullet_points": [
      "NeurIPS 2025 includes Startup & Innovation track with VC pitch nights."
    ],
    "contradictions": [],
    "gaps": []
  }
}
```

---

## 🔄 Iteration Loop

1. **Collector** → runs search, stores results in EvidenceStore.  
2. **Editor** → drafts narrative from latest evidence pack.  
3. **Auditor** → checks draft against all sources, updates contradictions/gaps.  
4. **Specialist** → enriches draft with domain insights.  
5. **Supervisor** → scores draft, provides feedback, decides continuation.  
6. **Loop Control** → refines query, Collector refreshes search, repeat until score ≥ 4 or max rounds.

---

## 📊 Lessons Learned from v2 → v3

- **v2 Strengths**  
  - Compression kept token usage manageable.  
  - Supervisor rubric enforced professional tone.  
  - Debug + dashboard gave visibility into refinement quality.

- **v2 Limitations**  
  - Single generator role → stagnation after ~10 rounds.  
  - Supervisor feedback repeated without injecting new evidence.  
  - Long loops plateaued instead of improving.

- **v3 Improvements**  
  - Multi-role specialization prevents stagnation.  
  - EvidenceStore ensures persistent, structured source injection.  
  - Auditor + Specialist roles add rigor and depth.  
  - Supervisor enforces rubric but now benefits from richer drafts.

---

## 🚀 Next Steps

- Implement `parse_sources()` to convert Collector’s raw text into structured JSON.  
- Run deep queries (e.g., AI safety controversies, investment strategy).  
- Benchmark v3 against v2: compare iteration scores, source diversity, and final draft quality.  
- Extend role library (e.g., Statistician, Legal Analyst) for domain-specific tasks.  
- Add Markdown export with embedded charts for full deep review.

---

## ✅ Status

Sketch v3 is **in development**.  
It represents a major architectural pivot from linear loops to multi-role orchestration with persistent evidence storage.  
This version aims to deliver **professional-quality, self-defining answers** that evolve meaningfully across rounds.


