# Self-Refining LLM Chat System

A prototype chat system that combines **LM Studio**, **SearXNG**, and **Docker MCP tools** to create a self-refining retrieval-augmented generation (RAG) loop.  
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
4. **Docker MCP Tools** – Extend functionality for specialized tasks.

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
