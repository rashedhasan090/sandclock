# Sandclock

**Timebox a shell command. See what it touched.**

Sandclock runs any command under a hard wall-clock budget, then reports the **filesystem delta** under a watched directory: created, modified, and deleted paths — plus exit code, duration, and whether it timed out.

Built for AI agent sandboxes, flaky experiments, and “what did this script actually write?” moments — without standing up a full container.

Original work by [Md Rashedul Hasan](https://www.mdrashedulhasan.me).

## Why this is novel

Most tools do **one** of these:

- `timeout(1)` — kills a process, says nothing about the filesystem
- `inotifywait` / FS watchers — stream events, don’t wrap a command budget
- full sandboxes — heavyweight for a one-off experiment

Sandclock combines **command timeboxing + before/after FS snapshot** into a tiny stdlib-first CLI with optional **JSON** for agents.

## Install

```bash
pip install -e ".[dev]"
sandclock --help
```

## Usage

```bash
# Fail the command if it runs longer than 30 seconds; print FS delta
sandclock 30s -- pytest -q

# Two-minute build, watch ./tmp only
sandclock 2m --cwd ./tmp -- npm run build

# Machine-readable report (great for agents)
sandclock 10s --json -- python script.py
```

Duration forms: `30`, `30s`, `2m`, `1h`, `1h30m`.

### Exit codes

- The wrapped command’s exit code, when it finishes in time
- `124` if Sandclock killed it for exceeding the budget (same convention as GNU `timeout`)

### Useful flags

| Flag | Meaning |
|------|---------|
| `--cwd DIR` | Watch and run inside `DIR` (default `.`) |
| `--json` | JSON report on stdout |
| `--ignore GLOB` | Extra ignore pattern (repeatable) |
| `--hash-bytes N` | SHA-256 files ≤ N bytes for stronger modify detection (default 1MiB; `0` disables) |

Default ignores include `.git`, `node_modules`, `.venv`, `__pycache__`, and similar noise.

## Demo

```bash
# Create a scratch dir and let a command write a file
mkdir -p /tmp/sandclock-demo && cd /tmp/sandclock-demo
sandclock 5s --json -- python -c "open('hello.txt','w').write('hi')"
```

Or use the bundled example:

```bash
sandclock 5s -- python examples/touchy.py
```

## How it works

1. Snapshot relative paths under `--cwd` (size, mtime; SHA-256 for small files).
2. Run the command in that directory; on POSIX, use a new process group so timeouts can kill children.
3. Snapshot again and diff.
4. Print a human report or JSON.

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT. Copyright © 2026 Md Rashedul Hasan.
