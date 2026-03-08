## Plan: Selector Logging Hardening

Review confirms the repo has fallback selectors but no true self-healing, and its most fragile paths either bypass the shared selector config or detect a working fallback selector and then ignore it. Recommended approach: add centralized selector-attempt logging, reuse the selector that actually succeeded, and normalize the hardcoded session/helper paths onto the shared config selectors.

**Steps**
1. Phase 1: Normalize query input selection in `d:\Github\notebooklm-experts-skill\scripts\ask_question.py` by storing the selector that actually succeeded in the `QUERY_INPUT_SELECTORS` loop and passing that selector forward for typing and any follow-up interactions. This blocks later logging quality if skipped.
2. Phase 1: Add a small selector-attempt helper in `d:\Github\notebooklm-experts-skill\scripts\browser_utils.py` or `d:\Github\notebooklm-experts-skill\scripts\runtime_logging.py` that logs before each selector attempt and records per-selector outcomes (`attempt`, `success`, `failure`, `reason`). This should use existing `debug()` / `debug_kv()` infrastructure rather than inventing a separate logger.
3. Phase 1: Extend `d:\Github\notebooklm-experts-skill\scripts\browser_utils.py` interaction helpers so they can either accept the already-resolved selector or accept a selector list and return the successful selector/element. Log when an element is missing, invisible, or times out.
4. Phase 2: Refactor `d:\Github\notebooklm-experts-skill\scripts\browser_session.py` to import and use `QUERY_INPUT_SELECTORS` and `RESPONSE_SELECTORS` from `d:\Github\notebooklm-experts-skill\scripts\config.py` instead of hardcoded selector strings. This can run in parallel with step 5 once the shared helper shape is defined.
5. Phase 2: Instrument response polling and metadata/source-panel selector paths in `d:\Github\notebooklm-experts-skill\scripts\ask_question.py` and `d:\Github\notebooklm-experts-skill\scripts\notebook_manager.py` so logs capture which selector was tried, which one matched, and why each failure occurred. Add start-of-loop logging before selector scans and success/failure logging inside the loop bodies.
6. Phase 3: Keep `d:\Github\notebooklm-experts-skill\scripts\check_notebooks.py` aligned with the same helper pattern so validation logs mirror query logs, but treat this as secondary because its current selector usage is already less brittle.
7. Phase 3: Verify with wrapper-based debug runs such as `d:\Github\notebooklm-experts-skill\run.bat auth_manager.py validate --debug`, `d:\Github\notebooklm-experts-skill\run.bat notebook_manager.py add --url ... --debug`, and `d:\Github\notebooklm-experts-skill\run.bat ask_question.py --question "..." --debug` to confirm the emitted logs show selector attempts, failures, and the final winning selector.

**Relevant files**
- `d:\Github\notebooklm-experts-skill\scripts\config.py` — existing centralized selector lists to reuse rather than duplicate
- `d:\Github\notebooklm-experts-skill\scripts\ask_question.py` — currently finds a fallback selector but types with `QUERY_INPUT_SELECTORS[0]`
- `d:\Github\notebooklm-experts-skill\scripts\browser_utils.py` — best place for shared selector-attempt helpers and per-selector logging hooks
- `d:\Github\notebooklm-experts-skill\scripts\browser_session.py` — currently hardcodes query and response selectors and misses the English fallback
- `d:\Github\notebooklm-experts-skill\scripts\notebook_manager.py` — contains additional hardcoded source-panel selectors that need attempt logging
- `d:\Github\notebooklm-experts-skill\scripts\check_notebooks.py` — lower-risk consumer to align after the core flow is hardened
- `d:\Github\notebooklm-experts-skill\scripts\runtime_logging.py` — existing debug/log-file infrastructure to build on

**Verification**
1. Run `d:\Github\notebooklm-experts-skill\run.bat ask_question.py --debug --question "test"` and confirm logs include one line before each selector attempt and one result line per attempt.
2. Force fallback behavior by temporarily disabling the primary selector in a controlled test or using a notebook/page locale that hits a fallback selector, then confirm the successful fallback selector is reused for typing.
3. Run `d:\Github\notebooklm-experts-skill\run.bat notebook_manager.py add --debug --url "https://notebooklm.google.com/notebook/..."` and confirm expand/source selector attempts are visible in logs.
4. Run any legacy `browser_session.py`-dependent path and confirm it now honors shared config selectors instead of inline literals.

**Decisions**
- Included scope: selector-review findings, selector-attempt logging, fallback reuse, and normalization of hardcoded selector consumers.
- Excluded scope: true self-healing selector discovery, DOM-learning, automatic config rewriting, or telemetry persistence across runs.
- Recommendation: prefer helper-based instrumentation over scattering ad hoc `print()` calls so logs stay consistent across scripts.

**Further Considerations**
1. Logging format recommendation: use structured `debug_kv()` lines with fields like `context`, `selector`, `action`, `success`, and `reason` so future grep/debug sessions are easy.
2. If desired later, add a lightweight selector statistics summary at process end, but do not block the first pass on aggregate telemetry.