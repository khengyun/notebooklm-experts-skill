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

- **Source-grounded answers** — Gemini responds only from your NotebookLM documents, drastically reducing hallucinations.
- **Persistent auth** — authenticate once; sessions are saved across runs so you never log in again.
- **Notebook library** — add, remove, search, and switch active notebooks from the CLI.
- **Export notebooks** — dump your full library to JSON or CSV with a single command.
- **Import notebooks** — restore or merge a JSON/CSV export back into your library with conflict resolution (`merge` / `overwrite`).
- **Add web source** — automatically add any web URL or YouTube URL as a notebook source via browser automation.
- **Anti-detection browser** — powered by `patchright` (real Chrome, not Chromium) to avoid bot detection.
- **Isolated virtual environment** — all dependencies live under `.venv/`, never touching your global Python.
- **Cross-platform** — `run.bat` (Windows) and `run.sh` (Linux/macOS) wrappers included.


---

**Then reload your agent** (Cmd+R or restart VS Code)
