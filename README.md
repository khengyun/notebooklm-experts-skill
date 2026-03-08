# NotebookLM Experts

Connect GitHub Copilot to Google NotebookLM for explicit, source-grounded queries against notebooks the user has already prepared.

This repository is a **skill package** for agent workflows. It helps the agent query NotebookLM and manage local notebook access, but it does **not** replace the agent's planning, follow-up, or synthesis.

## What This Repository Is

- A NotebookLM connector workflow for GitHub Copilot
- A local skill with query, auth, profile, and notebook-library operations
- A way to keep answers grounded in NotebookLM sources selected by the user

## What This Repository Is Not

- Not a standalone chat application
- Not an MCP server for NotebookLM
- Not an autonomous research system
- Not a replacement for the agent's reasoning or final response generation

---

## Quick Install

Paste this into GitHub Copilot chat:

```text
Install this skill: https://gist.github.com/khengyun/3ad656c8b9eea4f1c141389c962f5297
```

The agent will:

- Clone this repository
- Install it into the correct skills directory
- Verify the installation
- Show the next steps

Supported agents:

- GitHub Copilot

---

## Core Capabilities

### Querying

- Ask explicit questions against a selected NotebookLM notebook
- Retrieve answers grounded in NotebookLM sources
- Run follow-up questions one step at a time under agent control

### Profiles and Authentication

- Create and switch local auth profiles
- Reuse saved browser state across runs
- Validate or refresh authentication when needed

### Local Notebook Library

- Add, list, search, activate, and remove notebooks
- Keep a local library per profile
- Use an active notebook as the default query target

### Advanced Library Operations

- Export and import the local notebook library
- Add a web or YouTube URL as a NotebookLM source through the library workflow
- Inspect library statistics and clean local skill data

### Local Runtime

- Uses an isolated `.venv/`
- Uses `patchright` with Google Chrome
- Supports `run.bat` on Windows and `run.sh` on Linux/macOS

---

## High-Level Flow

1. Install the skill with `python install.py`.
2. Authenticate a profile with `auth_manager.py setup`.
3. Add or activate a notebook in the local library.
4. Ask an explicit question with `ask_question.py --question ...`.
5. Let the agent decide whether follow-up questions or synthesis are needed.

For the full operating contract, read `SKILL.md`.

---

## Example Commands

```bat
:: Install once
python install.py

:: Authenticate
.\run.bat auth_manager.py setup --name "My Account"

:: Add a notebook
.\run.bat notebook_manager.py add --url "https://notebooklm.google.com/notebook/..."

:: Ask a question
.\run.bat ask_question.py --question "What does this notebook say about authentication?"
```

Use the wrapper scripts for normal operations so commands run inside the skill's `.venv`.

---

## Limitations

- Each query opens a fresh browser session
- The user must upload source material to NotebookLM separately
- Free Google accounts may hit query limits
- Browser automation adds some latency per question

---

## Read Next

- `SKILL.md` - skill contract, boundaries, methods, and operating flow
- `references/api-reference.md` - CLI and script reference
- `references/usage_patterns.md` - workflow examples
- `references/best-practices.md` - question and library guidance
- `references/troubleshooting.md` - auth, browser, and rate-limit fixes
