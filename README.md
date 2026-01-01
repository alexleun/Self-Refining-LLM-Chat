# Sketch v4 architecture and runnable scaffold

This is a complete draft of Sketch v4: a human-like, milestone-driven research system with plan-first orchestration, multi-document collection (agentic RAG), sectional drafting and audits, artifact persistence, and compact logging/token accounting. Drop-in runnable scaffold is included.

---

## Design overview

- Plan-first orchestration: Planner and Decomposer produce goals, milestones, and a task graph (sections, dependencies, metrics).
- Agentic RAG Collector: Multi-document harvesting via web search + deep visit and local file ingestion; saves every document as a JSON artifact in project/evidence. Compression preserves facts.
- Sectional drafting and audits: Draft per section against evidence. Audit for contradictions and unsupported claims. Specialist enriches. Supervisor scores. Fulfillment checks. Critical Thinker challenges assumptions.
- Artifacts and reuse: Every stage writes artifacts in a project folder. Roles can reload artifacts anytime—this breaks reliance on parametric model memory.
- Token/log discipline: Compact per-round summary lines and token counts; per-role usage stored in memory.

---

## Project layout

- project_id/
  - plan.json — planning goals, milestones
  - tasks.json — task graph: sections, dependencies, metrics
  - evidence/
    - doc_x.json — one file per collected document (web/local), with metadata and compressed snippet
  - sections/
    - {section_id}/
      - draft_roundN.md
      - audit_roundN.md
      - score_roundN.json
      - fulfillment_roundN.md
      - critical_roundN.md
  - final_report.md
  - history.json — per-round summaries
  - manifest.json — artifact index and hashes
---

## Notes and suggested next enhancements

- Retriever and indexing: Add a simple keyword/embedding retriever to rank evidence per section query. Store embeddings in evidence JSON.
- Milestone scheduler: Activate sections based on dependencies, spreading work across rounds.
- Evidence citation scaffolding: Inline citations with stable keys referencing evidence files; automatic bibliography in final_report.md.
- Figures support: Define a figure generator role that writes chart specs (e.g., Vega-Lite JSON) saved in project/figures for inclusion.
- Local corpus ingestion: Extend local ingestion to PDFs with text extraction, and CSVs for chart generation.

This v4 draft gives you a real, transparent development cycle: collect many documents, save them, reference them across roles, and loop only as needed—closer to how you work when research actually matters.
