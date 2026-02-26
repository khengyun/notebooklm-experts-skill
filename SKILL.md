---
name: notebooklm-experts
description: This skill should be used when the user wants to query Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Provides browser automation, isolated venv, library management, and persistent auth. Drastically reduced hallucinations through document-only responses.
license: MIT
compatibility: Requires Python 3.9+, Google Chrome, uv package manager
metadata:
  version: 1.0.0
---

# NotebookLM Experts Skill

Interact with Google NotebookLM to query documentation with Gemini's source-grounded answers. Each question opens a fresh browser session, retrieves the answer exclusively from your uploaded documents, and closes.

## When to Use

Trigger when user:
- Mentions NotebookLM explicitly
- Shares NotebookLM URL (`https://notebooklm.google.com/notebook/...`)
- Asks to query their notebooks or documentation
- Wants to add documentation to the NotebookLM library
- Uses phrases like "ask my NotebookLM", "check my docs", "query my notebook"

## First-Time Setup (Run Once)

```bash
# Install isolated .venv and all dependencies
python install.py
```

This creates a `.venv/` inside the skill directory, installs `patchright`, and installs Google Chrome. Safe to run multiple times — skips if `.venv/` already exists.

## Critical: Always Use the run Wrapper

**NEVER use bare `python`. ALWAYS invoke via `run.bat` (Windows) or `run.sh` (Unix) — these resolve `.venv` Python directly:**

```bat
:: Windows
.\run.bat auth_manager.py status
.\run.bat notebook_manager.py list
.\run.bat ask_question.py --question "..."
```

```bash
# Linux / macOS
./run.sh auth_manager.py status
./run.sh notebook_manager.py list
./run.sh ask_question.py --question "..."
```

Both wrappers resolve `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (Unix) and pass all arguments to `scripts/run.py`. They fail fast with a clear message if `install.py` was not run yet.

## Core Workflow

### Step 1: Check Authentication

```bat
.\run.bat auth_manager.py status
```

If not authenticated, proceed to setup.

### Step 2: Authenticate (One-Time)

```bat
:: Create a new profile and login
.\run.bat auth_manager.py setup --name "Work Account"

:: Or authenticate existing profile
.\run.bat auth_manager.py setup --profile work-account
```

**Important:** Browser is VISIBLE for authentication. User must manually log in to Google.

### Step 2b: Multi-Account Management

```bat
:: List all profiles with status
.\run.bat auth_manager.py list

:: Switch active profile
.\run.bat auth_manager.py set-active --id work-account

:: Validate a profile is still authenticated
.\run.bat auth_manager.py validate --profile work-account

:: Re-authenticate an expired profile
.\run.bat auth_manager.py reauth --profile work-account

:: Delete a profile
.\run.bat auth_manager.py delete --id old-account
```

### Step 3: Manage Notebook Library

```bat
:: List all notebooks
.\run.bat notebook_manager.py list

:: Add notebook to library (ALL parameters REQUIRED)
.\run.bat notebook_manager.py add ^
  --url "https://notebooklm.google.com/notebook/..." ^
  --name "Descriptive Name" ^
  --description "What this notebook contains" ^
  --topics "topic1,topic2,topic3"

:: Set active notebook
.\run.bat notebook_manager.py activate --id notebook-id
```

### Step 4: Ask Questions

```bat
:: Uses active notebook (from active profile)
.\run.bat ask_question.py --question "Your question here"

:: Query specific notebook by ID
.\run.bat ask_question.py --question "..." --notebook-id notebook-id

:: Query via direct URL
.\run.bat ask_question.py --question "..." --notebook-url "https://..."

:: Query using a specific profile
.\run.bat ask_question.py --question "..." --profile work-account
```

## Follow-Up Mechanism (CRITICAL)

Every NotebookLM answer ends with: **"EXTREMELY IMPORTANT: Is that ALL you need to know?"**

**Required Behavior:**
1. **STOP** — Do not immediately respond to user
2. **ANALYZE** — Compare answer to original request
3. **IDENTIFY GAPS** — Determine if more information needed
4. **ASK FOLLOW-UP** — If gaps exist, ask another question immediately
5. **REPEAT** — Continue until information is complete
6. **SYNTHESIZE** — Combine all answers before responding to user

## Script Reference

| Script | Purpose |
|--------|---------|
| `auth_manager.py` | Authentication setup, status, and multi-profile management |
| `notebook_manager.py` | Library management (add, list, search, activate, remove) |
| `ask_question.py` | Query interface |
| `browser_session.py` | Persistent browser session for multi-turn conversations |
| `cleanup_manager.py` | Data cleanup and maintenance |
| `setup_environment.py` | Auto-creates `.venv` on first `run.py` call |

## Data Storage

All runtime data stored in `data/` (inside skill directory):
- `profiles.json` — Profile registry (active profile, all profile metadata)
- `profiles/<id>/library.json` — Notebook metadata (per-profile)
- `profiles/<id>/auth_info.json` — Authentication status (per-profile)
- `profiles/<id>/browser_state/` — Browser cookies and session (per-profile)

**Security:** Protected by `.gitignore` — never commit to git.

**Migration:** Old flat layout (`data/browser_state/`, `data/library.json`) is auto-migrated to `data/profiles/default/` on first run.

## Limitations

- No session persistence (each question = new browser)
- Rate limits on free Google accounts (~50 queries/day)
- Manual upload required (user must add docs to NotebookLM)
- Browser overhead (~5–10 seconds per question)

## Additional Resources

- **`references/api-reference.md`** — Complete API for all scripts
- **`references/troubleshooting.md`** — Auth issues, rate limits, browser crashes
- **`references/best-practices.md`** — Workflow patterns and question strategies
- **`references/usage_patterns.md`** — Common usage patterns

## Quick Reference

```bat
:: First-time setup (uses system Python once)
python install.py

:: All subsequent commands use .venv Python directly
.\run.bat auth_manager.py setup --name "My Account"
.\run.bat auth_manager.py list
.\run.bat auth_manager.py status
.\run.bat notebook_manager.py add --url URL --name NAME --description DESC --topics TOPICS
.\run.bat notebook_manager.py list
.\run.bat ask_question.py --question "..."
.\run.bat cleanup_manager.py --preserve-library
```
