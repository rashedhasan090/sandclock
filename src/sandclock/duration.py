"""Parse human durations like 30s, 2m, 1h into seconds."""

from __future__ import annotations

import re

_DURATION = re.compile(
    r"^\s*(?:(?P<hours>\d+)\s*h)?\s*(?:(?P<minutes>\d+)\s*m)?\s*(?:(?P<seconds>\d+)\s*s)?\s*$",
    re.IGNORECASE,
)
_PLAIN = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)\s*$")


def parse_duration(text: str) -> float:
    """Return duration in seconds.

    Accepts ``30``, ``30s``, ``2m``, ``1h``, ``1h30m``, ``90s``.
    """
    raw = text.strip()
    if not raw:
        raise ValueError("duration is empty")

    plain = _PLAIN.match(raw)
    if plain:
        return float(plain.group("seconds"))

    match = _DURATION.match(raw)
    if not match or not any(match.group(g) for g in ("hours", "minutes", "seconds")):
        raise ValueError(
            f"invalid duration {text!r}; use Ns, Nm, Nh, combinations like 1h30m, or plain seconds"
        )

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("duration must be positive")
    return float(total)
