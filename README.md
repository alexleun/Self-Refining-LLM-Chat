# Self-Refining LLM Chat System

A prototype chat system that combines **LM Studio**, **SearXNG**, and **Docker MCP tools** to create a self-refining retrieval-augmented generation (RAG) loop.  
The system uses an LLM both as a **worker** (search + summarize) and as a **supervisor** (review + refine), iterating until the response meets quality standards.

---

## ✨ Features
- **Intent Analysis**: LLM interprets user requests and generates search keywords.
- **Search Integration**: Queries SearXNG (`http://localhost:8888`) for fresh results.
- **Summarization**: LLM condenses retrieved information into clear answers.
- **Self-Review Loop**: LLM critiques its own output and refines queries until results are sufficient.
- **Conversation Continuation**: Distinguishes between *new queries* and *follow-up questions* to avoid redundant searches.
- **Tool Integration**: Docker MCP provides external capabilities (scraping, file access, APIs).

---

## 🏗️ Architecture
1. **LM Studio** – Local LLM server (`http://localhost:1234`) running `openai/gpt-oss-20b`.
2. **SearXNG** – Local meta-search engine (`http://localhost:8888`) with JSON API (`format=json`).
3. **Controller Script** – Python orchestrator that manages the loop.
4. **Conversation State Manager** – Tracks last query, keywords, results, and summary to decide whether to search again or continue.
5. **Docker MCP Tools** – Extend functionality for specialized tasks.

---

## 🔄 Conversation Flow

### Mode 1: New Search
- User asks a fresh question.
- LLM generates search keywords.
- SearXNG queried for results.
- LLM summarizes results.
- Supervisor loop reviews and refines until “good enough.”
- Answer returned to user.

### Mode 2: Continuation
- User asks a follow-up (e.g., “tell me more about NeurIPS”).
- No new search triggered.
- LLM uses **previous summary + new user message**.
- Supervisor loop refines reasoning only.
- Answer returned to user.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- LM Studio running in API server mode
- SearXNG running locally on port `8888`
- Docker MCP server available for tool calls

### Installation
```bash
git clone <your-private-repo-url>
cd Self-Refing-LLM-Chat-System
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

Run
python Sketch.py



📌 Roadmap
- [ ] Add structured parsing of SearXNG results (titles, URLs, snippets).
- [ ] Integrate Docker MCP tools for deeper data collection.
- [ ] Implement logging with configurable verbosity.
- [ ] Build a simple web UI for interactive chat.
- [ ] Enhance intent classification with fine-tuned prompts.

📜 License
Private repository – internal use only.
