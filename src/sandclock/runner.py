"""Run a command under a wall-clock timeout."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence

TIMEOUT_EXIT = 124


@dataclass
class RunResult:
    argv: List[str]
    exit_code: int
    timed_out: bool
    duration_sec: float


def _on_posix() -> bool:
    return os.name == "posix"


def run_timed(
    argv: Sequence[str],
    *,
    cwd: Optional[str] = None,
    timeout_sec: float,
) -> RunResult:
    if not argv:
        raise ValueError("command is empty")

    kwargs = {
        "cwd": cwd,
    }
    if _on_posix():
        # New session so we can kill the whole process group on timeout.
        kwargs["start_new_session"] = True

    started = time.monotonic()
    proc = subprocess.Popen(list(argv), **kwargs)
    timed_out = False
    try:
        proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill(proc)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _kill(proc, force=True)
            proc.wait()
    duration = time.monotonic() - started
    code = TIMEOUT_EXIT if timed_out else int(proc.returncode if proc.returncode is not None else 1)
    return RunResult(argv=list(argv), exit_code=code, timed_out=timed_out, duration_sec=duration)


def _kill(proc: subprocess.Popen, force: bool = False) -> None:
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        if _on_posix() and proc.pid:
            os.killpg(proc.pid, sig)
        else:
            if force:
                proc.kill()
            else:
                proc.terminate()
    except ProcessLookupError:
        return
    except OSError:
        try:
            proc.kill()
        except OSError:
            return
