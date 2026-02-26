# NotebookLM Experts

Query Google NotebookLM notebooks directly from your AI agent for source-grounded, citation-backed answers powered by Gemini. Each question spins up an isolated browser session, retrieves the answer exclusively from your uploaded documents, and exits cleanly — drastically reducing hallucinations through document-only responses.

---

## Features

- **Source-grounded answers** — Gemini responds only from your NotebookLM documents
- **Isolated virtual environment** — dependencies are contained under `.venv/`, never touching your global Python
- **Persistent auth** — authenticate once; sessions are saved across runs
- **Notebook library** — manage multiple notebooks; switch active notebook anytime
- **Anti-detection browser** — powered by `patchright` (real Chrome, not Chromium)
- **Cross-platform** — `run.bat` (Windows) and `run.sh` (Linux/macOS) wrappers
