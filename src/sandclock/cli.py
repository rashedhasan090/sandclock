"""Sandclock command-line entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from sandclock import __version__
from sandclock.duration import parse_duration
from sandclock.fsdelta import DEFAULT_IGNORES, diff, snapshot
from sandclock.runner import TIMEOUT_EXIT, run_timed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sandclock",
        description=(
            "Timebox a shell command and report the filesystem delta "
            "under a watched directory."
        ),
        epilog="Example: sandclock 30s -- pytest -q",
    )
    parser.add_argument(
        "duration",
        help="Wall-clock budget: 30, 30s, 2m, 1h, or 1h30m",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after -- (recommended) or as remaining args",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Directory to watch and to use as the command working directory (default: .)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        metavar="GLOB",
        help="Extra ignore glob (repeatable). Defaults already skip .git, node_modules, venvs, etc.",
    )
    parser.add_argument(
        "--hash-bytes",
        type=int,
        default=1_048_576,
        metavar="N",
        help="SHA-256 files up to N bytes for stronger modify detection (default: 1048576). 0 disables.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _normalize_command(raw: Sequence[str]) -> List[str]:
    argv = list(raw)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        raise SystemExit("sandclock: missing command after duration (try: sandclock 10s -- echo hi)")
    return argv


def _human_report(
    *,
    argv: List[str],
    exit_code: int,
    timed_out: bool,
    duration_sec: float,
    created: List[str],
    modified: List[str],
    deleted: List[str],
) -> str:
    lines = [
        f"command: {' '.join(argv)}",
        f"duration: {duration_sec:.3f}s",
        f"exit: {exit_code}" + (" (timed out)" if timed_out else ""),
        f"created ({len(created)}):",
    ]
    lines.extend(f"  + {p}" for p in created) if created else lines.append("  (none)")
    lines.append(f"modified ({len(modified)}):")
    lines.extend(f"  ~ {p}" for p in modified) if modified else lines.append("  (none)")
    lines.append(f"deleted ({len(deleted)}):")
    lines.extend(f"  - {p}" for p in deleted) if deleted else lines.append("  (none)")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        timeout = parse_duration(args.duration)
    except ValueError as exc:
        print(f"sandclock: {exc}", file=sys.stderr)
        return 2

    command = _normalize_command(args.command)
    root = Path(args.cwd).expanduser().resolve()
    if not root.is_dir():
        print(f"sandclock: cwd is not a directory: {root}", file=sys.stderr)
        return 2

    ignores = list(DEFAULT_IGNORES) + list(args.ignore)
    before = snapshot(root, ignore=ignores, hash_bytes=args.hash_bytes)
    result = run_timed(command, cwd=str(root), timeout_sec=timeout)
    after = snapshot(root, ignore=ignores, hash_bytes=args.hash_bytes)
    delta = diff(before, after)

    report = {
        "command": result.argv,
        "cwd": str(root),
        "timeout_sec": timeout,
        "duration_sec": round(result.duration_sec, 6),
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "created": delta.created,
        "modified": delta.modified,
        "deleted": delta.deleted,
        "timeout_exit_code": TIMEOUT_EXIT,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            _human_report(
                argv=result.argv,
                exit_code=result.exit_code,
                timed_out=result.timed_out,
                duration_sec=result.duration_sec,
                created=delta.created,
                modified=delta.modified,
                deleted=delta.deleted,
            )
        )

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
