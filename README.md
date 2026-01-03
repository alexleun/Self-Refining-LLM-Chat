# Self-Refining LLM Chat System

A prototype chat system that combines **LM Studio**, **SearXNG** to create a self-refining retrieval-augmented generation (RAG) loop.  
The system uses an LLM both as a **worker** (search + summarize) and as a **supervisor** (review + refine), iterating until the response meets quality standards.

---

## ✨ Features
- **Intent Analysis**: LLM interprets user requests and generates search keywords.
- **Search Integration**: Queries SearXNG (`http://localhost:8888`) for fresh results.
- **Summarization**: LLM condenses retrieved information into clear answers.
- **Self-Review Loop**: LLM critiques its own output and refines queries until results are sufficient.
- **Tool Integration**: Docker MCP provides external capabilities (scraping, file access, APIs).

---

## 🏗️ Architecture
1. **LM Studio** – Local LLM server (`http://localhost:1234`) running `openai/gpt-oss-20b`.
2. **SearXNG** – Local meta-search engine (`http://localhost:8888`) with JSON API.
3. **Controller Script** – Python orchestrator that manages the loop.

---

# Self-Refining LLM Chat Orchestration

A modular, multi‑role orchestration framework for large language models (LLMs).  
This project demonstrates how to coordinate specialized roles (Planner, Decomposer, Collector, Editor, Auditor, Specialist, Supervisor, Fulfillment Checker, Critical Thinker, Integrator) into a reproducible pipeline that produces professional, evidence‑driven reports.

---

## ✨ Features

- **Role‑based modular design**  
  Each role lives in its own Python module (`roles/`), making it easy to extend or swap logic independently.

- **Agentic RAG (Retrieval‑Augmented Generation)**  
  Evidence collection from web search (via SearXNG), deep fetch, and local file ingestion.  
  Adaptive semantic compression ensures factual detail is preserved while reducing token usage.

- **Iterative refinement loop**  
  Multi‑round drafting, auditing, enrichment, scoring, and fulfillment checks until quality thresholds are met.

- **Executive summary & integration**  
  Automatic generation of board‑ready summaries and integrated Markdown reports, preserving diagrams (Mermaid syntax).

- **Transparency & auditability**  
  - Iteration history saved (`history.json`)  
  - Evidence pool persisted (`evidence_pool.json`)  
  - Token usage tracked per role  
  - Logs written to both file (`sketch_v4.log`) and console

- **Monitoring & feedback**  
  - Nested progress bars (`tqdm`) for rounds and sections  
  - Color‑coded console summaries (green/yellow/red) for quality  
  - Final outcome banner + token usage summary

---

## 📂 Project Structure

```
sketch_v4/
│
├── main.py               # CLI harness
├── orchestrator.py       # Orchestrator class
│
├── roles/                # Role modules
│   ├── planner.py
│   ├── decomposer.py
│   ├── collector.py
│   ├── editor.py
│   ├── auditor.py
│   ├── specialist.py
│   ├── supervisor.py
│   ├── fulfillment.py
│   ├── critical.py
│   └── integrator.py
│
└── utils/                # Utilities
    ├── config.py
    ├── helpers.py
    ├── token_counter.py
    ├── persistence.py
    └── logging_utils.py
```

---

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/self-refining-llm-chat.git
   cd self-refining-llm-chat
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Required packages: `requests`, `tqdm`, `colorama`, `dataclasses` (Python 3.7+ includes it).

3. **Run the CLI harness**
   ```bash
   python main.py
   ```

4. **Monitor progress**
   - Console: progress bars + color‑coded summaries  
   - Log file: `sketch_v4.log`  

5. **Check outputs**
   - `final_report.md` → integrated professional report  
   - `executive_summary.md` → board‑ready summary  
   - `history.json` → iteration history  
   - `evidence_pool.json` → collected evidence  
   - `manifest.json` → artifact manifest  

---

## 🛠 Configuration

Edit `utils/config.py` to adjust:
- `LM_STUDIO_URL` → local LM Studio endpoint  
- `SEARX_URL` → SearXNG search endpoint  
- `LLM_CFG` → max tokens, timeout  
- `ROLE_TEMPS` → per‑role temperature settings  

---

## 📊 Example Output

Console:

```
Orchestration rounds:  33%|█████████▎                | 1/3 [00:15<00:30, 15.0s/round]
Round 1 sections:     100%|█████████████████████████| 3/3 [00:12<00:00,  4.00s/section]
Round 1 summary: avg_overall=7.25, improvements=2, tokens_used=450   ← (yellow text)

============================================================
⚠️ REVIEW: Report acceptable but improvements suggested
============================================================

============================================================
📊 TOKEN USAGE SUMMARY
============================================================
Total tokens used: 1450
Per-role breakdown:
  planner      prompt=120 completion=300 total=420
  editor       prompt=200 completion=400 total=600
  supervisor   prompt=80  completion=10  total=90
```

---

## 🤝 Contributing

This project is open to requests and contributions.  
Ideas welcome for:
- New specialized roles (e.g. Scenario Mapper, Diagram Generator)  
- Improved scoring rubrics  
- Alternative evidence sources  
- Visualization integration  

Fork, open issues, or submit PRs — let’s refine this orchestration together.
