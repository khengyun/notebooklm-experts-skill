---
name: notebooklm-experts-skill
description: This skill connects GitHub Copilot to Google NotebookLM for explicit, source-grounded queries against notebooks the user has already prepared. The agent remains responsible for planning, follow-up, and synthesis.
license: MIT
compatibility: Requires Python 3.9+ and Google Chrome
metadata:
  version: 1.0.0
  methods:
    - query
    - library
---

# NotebookLM Experts Skill

Use this skill when the agent needs to ask explicit questions against a user's Google NotebookLM notebooks and return source-grounded answers. Each query opens a fresh browser session, sends a single question, retrieves the result, and exits.

## What This Skill Does

- Runs explicit NotebookLM queries against a selected notebook
- Manages local auth, profiles, and notebook library metadata
- Helps the agent keep answers grounded in NotebookLM sources

## What This Skill Does Not Do

- It does **not** replace the agent's reasoning or synthesis
- It does **not** run autonomous research across notebooks
- It does **not** act as a standalone application or hosted service
- It does **not** provide MCP connectivity to NotebookLM

## Role and Boundaries

This repository is a **skill package**, not a standalone app or MCP server.

- The skill executes constrained NotebookLM operations such as auth, notebook selection, and explicit queries.
- The agent decides when to call the skill, what to ask, and whether more follow-up is needed.
- The agent is responsible for comparing answers, filling gaps, and composing the final response.
- The skill should be treated as a connector workflow, not as an autonomous investigation system.

## When to Use

Trigger this skill when the user:

- Mentions NotebookLM explicitly
- Shares a NotebookLM URL like `https://notebooklm.google.com/notebook/...`
- Wants answers grounded in documents already uploaded to NotebookLM
- Wants to manage their local NotebookLM notebook library or auth profiles
- Uses phrases like `ask my NotebookLM`, `check my docs`, or `query my notebook`

## When Not to Use

Do not use this skill when the task is:

- General web research outside NotebookLM
- Open-ended multi-source investigation without explicit NotebookLM notebooks
- Pure reasoning, synthesis, or implementation work that does not require NotebookLM
- Unrelated to the user's NotebookLM content or local notebook library

## Available Methods

| Method | Purpose | Use When |
|--------|---------|----------|
| **query** | Ask a focused question against one notebook | The user needs a source-grounded answer from a selected notebook |
| **library** | Manage local notebook and profile state | The user needs to add, activate, search, export, import, or organize notebooks |

## First-Time Setup

```bash
python install.py
```

This creates a local `.venv/`, installs dependencies, and installs Google Chrome for `patchright`.

## Always Use the Wrapper

Do not use bare `python` for skill operations. Use `run.bat` on Windows or `run.sh` on Linux/macOS so commands run inside the skill's `.venv`.

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

Both wrappers route to `scripts/run.py` and fail fast if the environment has not been installed yet.

## Core Operating Flow

### 1. Check authentication

```bat
.\run.bat auth_manager.py status
```

If no valid session exists, continue to authentication.

### 2. Authenticate a profile

```bat
:: Create a new profile and authenticate it
.\run.bat auth_manager.py setup --name "Work Account"

:: Or authenticate an existing profile
.\run.bat auth_manager.py setup --profile work-account
```

Authentication is interactive. The browser must stay visible so the user can sign in to Google.

### 3. Optional profile helper flow

If the user wants a guided profile creation flow, use:

```bat
.\run.bat add_profile.py
```

This helper script creates a profile, opens a visible browser for login, and returns a usable profile ID.

### 4. Register or activate notebooks

```bat
:: List known notebooks
.\run.bat notebook_manager.py list

:: Add a notebook to the local library
.\run.bat notebook_manager.py add ^
  --url "https://notebooklm.google.com/notebook/..."

:: Add with explicit metadata if needed
.\run.bat notebook_manager.py add ^
  --url "https://notebooklm.google.com/notebook/..." ^
  --name "Descriptive Name" ^
  --description "What this notebook contains" ^
  --topics "topic1,topic2,topic3"

:: Set the active notebook
.\run.bat notebook_manager.py activate --id notebook-id
```

`--name`, `--description`, and `--topics` can be supplied explicitly or inferred by the library workflow when metadata fetching is available.

### 5. Ask explicit questions

```bat
:: Use the active notebook
.\run.bat ask_question.py --question "Your question here"

:: Query a specific notebook by ID
.\run.bat ask_question.py --question "..." --notebook-id notebook-id

:: Query a direct NotebookLM URL
.\run.bat ask_question.py --question "..." --notebook-url "https://..."

:: Use a specific profile
.\run.bat ask_question.py --question "..." --profile work-account

:: Refresh a stored notebook name without asking a question
.\run.bat ask_question.py --notebook-id notebook-id --refresh-name-only
```

### 6. Example agent-led follow-up loop

When deeper analysis is needed, the agent should stay in control and ask explicit follow-up questions step by step.

```bat
:: Step A: broad question
.\run.bat ask_question.py --question "Give me an overview of authentication in this doc"

:: Step B: targeted follow-up
.\run.bat ask_question.py --question "What constraints and edge cases are listed?"

:: Step C: switch notebooks for comparison
.\run.bat notebook_manager.py activate --id notebook-id-2
.\run.bat ask_question.py --question "How does this doc differ on auth strategy?"
```

The skill returns query results. The agent performs the comparison and final synthesis in chat.

## Additional Library Operations

Use the `library` method for local notebook management tasks such as:

- `notebook_manager.py search`
- `notebook_manager.py export`
- `notebook_manager.py import`
- `notebook_manager.py add-source`
- `notebook_manager.py stats`
- `notebook_manager.py remove`

These are support operations around the local notebook library. They do not change the core role of the skill.

## Recommended Follow-Up Pattern

NotebookLM answers end with a reminder to check whether more information is needed. Treat that as an agent prompt to review completeness before answering the user.

Recommended agent behavior:

1. Stop before replying to the user.
2. Compare the NotebookLM answer to the original request.
3. Identify missing details, edge cases, or comparison points.
4. Ask another explicit NotebookLM question if gaps remain.
5. Repeat until the answer set is complete enough.
6. Synthesize the final response in chat.

## Script Reference

| Script | Purpose |
|--------|---------|
| `add_profile.py` | Guided helper for creating and authenticating a new profile |
| `ask_question.py` | Query a notebook with one explicit question |
| `notebook_manager.py` | Manage the local notebook library |
| `auth_manager.py` | Set up, validate, switch, and clear auth profiles |
| `cleanup_manager.py` | Clean local skill data and temporary files |
| `check_notebooks.py` | Validate notebook links in the local library |
| `debug_skill.py` | Run smoke tests across the skill layers |

## Data Storage

All runtime data is stored under `data/` inside the skill directory:

- `profiles.json` - profile registry
- `profiles/<id>/library.json` - notebook metadata for that profile
- `profiles/<id>/auth_info.json` - auth status for that profile
- `profiles/<id>/browser_state/` - cookies and session data for that profile

This data is local-only and should remain ignored by git.

## Limitations

- Each question opens a new browser session
- Free Google accounts may hit query rate limits
- The user must upload source material to NotebookLM separately
- Browser automation adds several seconds of overhead per query

## Additional Resources

- `references/api-reference.md` - CLI and script behavior reference
- `references/troubleshooting.md` - auth, browser, and rate-limit fixes
- `references/usage_patterns.md` - workflow examples
- `references/best-practices.md` - question and library guidance

## Quick Reference

```bat
:: Install once
python install.py

:: Authenticate
.\run.bat auth_manager.py setup --name "My Account"

:: Inspect profiles and notebooks
.\run.bat auth_manager.py list
.\run.bat notebook_manager.py list

:: Add a notebook
.\run.bat notebook_manager.py add --url URL

:: Query it
.\run.bat ask_question.py --question "Your question"

:: Clean temporary data while preserving library state
.\run.bat cleanup_manager.py --preserve-library
```
