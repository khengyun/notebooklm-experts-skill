#!/usr/bin/env python3
"""Shared runtime logging helpers for NotebookLM skill scripts."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_LOG_STATE = {
    "configured": False,
    "debug": False,
    "show_steps": False,
    "script_name": None,
    "log_path": None,
    "step_counter": 0,
    "log_handle": None,
    "stdout": None,
    "stderr": None,
}


class _TeeStream:
    """Mirror writes to the original stream and an optional log file."""

    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def write(self, data: str) -> int:
        written = self.primary.write(data)
        if self.secondary:
            self.secondary.write(data)
        return written

    def flush(self) -> None:
        self.primary.flush()
        if self.secondary:
            self.secondary.flush()

    def isatty(self) -> bool:
        return getattr(self.primary, "isatty", lambda: False)()


def extract_runtime_flags(argv: List[str]) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """Extract runtime flags from argv without constraining their position."""
    options: Dict[str, Optional[str]] = {
        "debug": False,
        "show_steps": False,
        "log_file": None,
    }
    cleaned: List[str] = []
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg == "--debug":
            options["debug"] = True
        elif arg == "--show-steps":
            options["show_steps"] = True
        elif arg == "--log-file":
            if i + 1 >= len(argv):
                raise ValueError("--log-file requires a path")
            options["log_file"] = argv[i + 1]
            i += 1
        elif arg.startswith("--log-file="):
            options["log_file"] = arg.split("=", 1)[1]
        else:
            cleaned.append(arg)
        i += 1

    return options, cleaned


def configure_runtime(
    script_name: str,
    *,
    debug: bool = False,
    show_steps: bool = False,
    log_file: Optional[str] = None,
) -> Optional[Path]:
    """Configure shared runtime logging for the current process."""
    if _LOG_STATE["configured"]:
        return _LOG_STATE["log_path"]

    log_path = None
    if debug or log_file:
        log_path = _resolve_log_path(script_name, log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = open(log_path, "a", encoding="utf-8")

        _LOG_STATE["log_handle"] = log_handle
        _LOG_STATE["stdout"] = sys.stdout
        _LOG_STATE["stderr"] = sys.stderr
        sys.stdout = _TeeStream(sys.stdout, log_handle)
        sys.stderr = _TeeStream(sys.stderr, log_handle)

    _LOG_STATE["configured"] = True
    _LOG_STATE["debug"] = bool(debug)
    _LOG_STATE["show_steps"] = bool(show_steps or debug)
    _LOG_STATE["script_name"] = script_name
    _LOG_STATE["log_path"] = log_path

    if debug:
        print(f"[debug] enabled for {script_name}")
    if log_path:
        print(f"[debug] log file: {log_path}")
    if _LOG_STATE["show_steps"]:
        print(f"[debug] step tracing enabled for {script_name}")

    return log_path


def runtime_options_help() -> str:
    """Return a short help string for shared runtime flags."""
    return "Runtime flags: --debug --show-steps --log-file <path>"


def step(message: str) -> None:
    """Print a high-level progress marker when step tracing is enabled."""
    if not _LOG_STATE["show_steps"]:
        return

    _LOG_STATE["step_counter"] += 1
    print(f"[step {_LOG_STATE['step_counter']:02d}] {message}")


def expect(message: str) -> None:
    """Describe the state the script is waiting for."""
    if _LOG_STATE["show_steps"] or _LOG_STATE["debug"]:
        print(f"[expect] {message}")


def debug(message: str) -> None:
    """Print a debug-only message."""
    if _LOG_STATE["debug"]:
        print(f"[debug] {message}")


def debug_kv(label: str, **values) -> None:
    """Print a structured key-value debug line."""
    if not _LOG_STATE["debug"]:
        return
    parts = [f"{key}={value!r}" for key, value in values.items()]
    payload = ", ".join(parts)
    print(f"[debug] {label}: {payload}")


def log_exception(prefix: str, exc: BaseException) -> None:
    """Print a concise exception line with debug context."""
    print(f"{prefix}: {exc}")
    if _LOG_STATE["debug"]:
        debug_kv("exception", type=type(exc).__name__, message=str(exc))


def _resolve_log_path(script_name: str, log_file: Optional[str]) -> Path:
    if log_file:
        return Path(log_file).expanduser().resolve()

    skill_dir = Path(__file__).parent.parent
    logs_dir = skill_dir / "data" / "logs"
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = script_name.replace(".py", "").replace("/", "-")
    return logs_dir / f"{safe_name}-{timestamp}.log"
