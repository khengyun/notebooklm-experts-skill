# NotebookLM Experts

Query Google NotebookLM notebooks directly from your AI agent for source-grounded, citation-backed answers powered by Gemini. Each question spins up an isolated browser session, retrieves the answer exclusively from your uploaded documents, and exits cleanly — drastically reducing hallucinations through document-only responses.

---

## 🚀 Quick Install

**Paste this into Claude Code, Copilot, or any AI agent chat:**

```
Install this skill: https://gist.github.com/khengyun/3ad656c8b9eea4f1c141389c962f5297
```

The agent will automatically:
- Clone this repository
- Install to the correct skills directory
- Verify installation
- Show next steps

**Supported agents**: Claude Code · GitHub Copilot · OpenAI Codex CLI · Gemini CLI

---

## Features

- **Source-grounded answers** — Gemini responds only from your NotebookLM documents
- **Isolated virtual environment** — dependencies are contained under `.venv/`, never touching your global Python
- **Persistent auth** — authenticate once; sessions are saved across runs
- **Notebook library** — manage multiple notebooks; switch active notebook anytime
- **Anti-detection browser** — powered by `patchright` (real Chrome, not Chromium)
- **Cross-platform** — `run.bat` (Windows) and `run.sh` (Linux/macOS) wrappers
