"""Filesystem snapshots and deltas."""

from __future__ import annotations

import fnmatch
import hashlib
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_IGNORES = (
    ".git",
    ".git/**",
    "__pycache__",
    "__pycache__/**",
    "*.pyc",
    ".venv",
    ".venv/**",
    "venv",
    "venv/**",
    "node_modules",
    "node_modules/**",
    ".pytest_cache",
    ".pytest_cache/**",
    ".mypy_cache",
    ".mypy_cache/**",
    ".tox",
    ".tox/**",
    "dist",
    "dist/**",
    "build",
    "build/**",
    "*.egg-info",
    "*.egg-info/**",
)


@dataclass(frozen=True)
class FileStat:
    size: int
    mtime_ns: int
    sha256: Optional[str] = None


@dataclass
class Delta:
    created: List[str]
    modified: List[str]
    deleted: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_ignored(rel: str, patterns: Iterable[str]) -> bool:
    name = Path(rel).name
    for pattern in patterns:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
            return True
        # Also match directory prefixes: pattern "node_modules" should skip "node_modules/x"
        if "/" not in pattern.rstrip("/") and (
            rel == pattern.rstrip("/") or rel.startswith(pattern.rstrip("/") + "/")
        ):
            return True
    return False


def _hash_file(path: Path, limit: int) -> Optional[str]:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > limit:
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(65536)
                if not chunk:
                    break
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def snapshot(
    root: Path,
    *,
    ignore: Iterable[str] = DEFAULT_IGNORES,
    hash_bytes: int = 1_048_576,
) -> Dict[str, FileStat]:
    root = root.resolve()
    patterns = list(ignore)
    out: Dict[str, FileStat] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        # prune ignored directories in-place
        keep: List[str] = []
        for d in dirnames:
            rel = _rel(base / d, root)
            if is_ignored(rel, patterns) or is_ignored(d, patterns):
                continue
            keep.append(d)
        dirnames[:] = keep
        for name in filenames:
            path = base / name
            rel = _rel(path, root)
            if is_ignored(rel, patterns):
                continue
            try:
                st = path.stat()
            except OSError:
                continue
            if not path.is_file():
                continue
            digest = _hash_file(path, hash_bytes) if hash_bytes > 0 else None
            out[rel] = FileStat(size=st.st_size, mtime_ns=st.st_mtime_ns, sha256=digest)
    return out


def diff(before: Dict[str, FileStat], after: Dict[str, FileStat]) -> Delta:
    created = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified: List[str] = []
    for key in sorted(set(before) & set(after)):
        a, b = before[key], after[key]
        if a.sha256 is not None and b.sha256 is not None:
            if a.sha256 != b.sha256:
                modified.append(key)
            continue
        if a.size != b.size or a.mtime_ns != b.mtime_ns:
            modified.append(key)
    return Delta(created=created, modified=modified, deleted=deleted)
