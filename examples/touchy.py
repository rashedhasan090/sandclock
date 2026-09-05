#!/usr/bin/env python3
"""Tiny demo script: creates, edits, and deletes files under cwd."""

from pathlib import Path

Path("created-by-touchy.txt").write_text("hello from touchy\n", encoding="utf-8")
already = Path("scratch.txt")
already.write_text("before\n", encoding="utf-8")
already.write_text("after\n", encoding="utf-8")
ephemeral = Path("ephemeral.txt")
ephemeral.write_text("bye\n", encoding="utf-8")
ephemeral.unlink()
print("touchy done")
