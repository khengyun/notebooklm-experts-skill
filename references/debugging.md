---
name: notebooklm-debugging
description: Per-layer debug workflow and recovery guide for the NotebookLM skill
---

# NotebookLM Skill — Debugging Guide

Run the smoke test first. It identifies exactly which layer is broken and prints the fix inline:

```bat
.\run.bat debug_skill.py               :: Quick check (no browser)
.\run.bat debug_skill.py --no-browser  :: Skip Chrome launch (fastest)
.\run.bat debug_skill.py --check-links :: Full check including notebook URLs
```

The runner checks 5 layers in order. A broken layer does not block the next unless noted.

---

## Layer 1: Environment

**Symptoms:** `ModuleNotFoundError`, `ImportError`, script refuses to start, `patchright` not found.

| Check | Fix |
|---|---|
| `.venv/` does not exist | `python install.py` |
| `patchright` not importable | `python install.py` |
| Chrome not installed | `python install.py` (installs Chrome via patchright) |
| `requirements.txt` missing | Restore from source control |

**Debug manually:**
```bat
.\.venv\Scripts\python.exe -c "import patchright; print('OK')"
.\.venv\Scripts\python.exe -c "from patchright.sync_api import sync_playwright; print('OK')"
```

**Root cause pattern:** Almost always means `install.py` was not run, or was run with whichever system Python instead of the venv Python.

---

## Layer 2: Auth

**Symptoms:** Redirected to `accounts.google.com`, "Not authenticated" error, blank page, login loop.

| Check | Fix |
|---|---|
| `state.json` does not exist | `.\run.bat auth_manager.py setup` |
| `state.json` is > 7 days old | `.\run.bat auth_manager.py reauth` |
| Wrong Google account logged in | `.\run.bat auth_manager.py setup` → log in to correct account |
| State file corrupt | Delete `data/browser_state/state.json` → re-run setup |

**Debug manually:**
```bat
.\run.bat auth_manager.py status
```

> **Critical:** Browser must be **visible** (not headless) during `setup`. The user must manually
> complete the Google login. Never call `setup` with `--headless`.

---

## Layer 3: Library

**Symptoms:** "No notebooks registered", "Notebook not found", `KeyError` on notebook ID, `library.json` JSON decode error.

| Check | Fix |
|---|---|
| Library empty | Add a notebook (see below) |
| No active notebook set | `.\run.bat notebook_manager.py activate --id <id>` |
| Active notebook has no URL | `.\run.bat notebook_manager.py update --id <id> --url <url>` |
| `library.json` corrupt | `.\run.bat cleanup_manager.py --preserve-library` then re-add |

**Add a notebook:**
```bat
.\run.bat notebook_manager.py add ^
  --url "https://notebooklm.google.com/notebook/..." ^
  --name "My Docs" ^
  --description "What this notebook contains" ^
  --topics "topic1,topic2"
```

**List all notebooks:**
```bat
.\run.bat notebook_manager.py list
```

---

## Layer 4: Browser

**Symptoms:** Chrome crash, timeout waiting for page, `BrowserType.launch_persistent_context` exception, skill opens then hangs.

| Check | Fix |
|---|---|
| Chrome executable missing | `python install.py` |
| Session expired (redirected to login) | `.\run.bat auth_manager.py reauth` |
| GPU / sandbox errors on server | Add `'--disable-gpu'` to `BROWSER_ARGS` in `scripts/config.py` |
| NotebookLM unreachable | Check network / VPN |
| Timeout on page load | Increase `PAGE_LOAD_TIMEOUT` in `scripts/config.py` |

**Debug with visible browser (headful):**
```bat
.\run.bat ask_question.py --question "ping" --headful
```
This opens Chrome visibly so you can see exactly what is happening on the page.

**Debug browser launch only:**
```python
# scripts/config.py — add to BROWSER_ARGS if on headless server
'--disable-gpu',
'--single-process',
```

---

## Layer 5: Notebook Links

**Symptoms:** Specific notebooks load to home page, `[INACTIVE]` on `check_notebooks.py` report.

| Status | Meaning | Fix |
|---|---|---|
| `active` | Notebook loads and input box is present | — |
| `inactive` | URL redirected to home (deleted or access lost) | Update or remove notebook |
| `error` | Exception during browser check | Verify URL format |

```bat
:: Validate all links
.\run.bat check_notebooks.py

:: Update a broken URL
.\run.bat notebook_manager.py update --id <id> --url <new-url>

:: Remove a permanently deleted notebook
.\run.bat notebook_manager.py remove --id <id>
```

**Valid NotebookLM URL format:**
```
https://notebooklm.google.com/notebook/<32-char-id>
```

---

## Full Reset (Last Resort)

Use when multiple layers are broken simultaneously.

```bat
:: Step 1: Clean all runtime data, keep library
.\run.bat cleanup_manager.py --preserve-library

:: Step 2: Re-authenticate
.\run.bat auth_manager.py setup

:: Step 3: Run smoke test to confirm
.\run.bat debug_skill.py
```

To also wipe the notebook library:
```bat
.\run.bat cleanup_manager.py
```

Then re-add notebooks via `notebook_manager.py add`.

---

## Reading Smoke Test Output

```
======================================================
  NotebookLM Skill — Smoke Test Runner
======================================================

Layer 1: Environment
  [PASS]  Virtual environment (.venv)  d:\...\notebooklm-experts\.venv
  [PASS]  patchright importable
  [PASS]  requirements.txt present

Layer 2: Auth
  [FAIL]  Auth state file (state.json)  state.json not found — never authenticated
         → Run:  .\run.bat auth_manager.py setup  (browser opens for Google login)

Layer 3: Library
  [WARN]  Notebook library  Library is empty — no notebooks registered
         → Run:  .\run.bat notebook_manager.py add ...
...
```

- **`[FAIL]`** — Critical issue, fix before using the skill.
- **`[WARN]`** — Skill may still work but degraded. Fix when convenient.
- **`[PASS]`** — Layer healthy.
- **`[SKIP]`** — Layer not checked (use `--check-links` or remove `--no-browser` to enable).
