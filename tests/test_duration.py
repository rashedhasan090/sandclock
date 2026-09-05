from sandclock.duration import parse_duration
import pytest


@pytest.mark.parametrize(
    "text,expected",
    [
        ("30", 30.0),
        ("30s", 30.0),
        ("2m", 120.0),
        ("1h", 3600.0),
        ("1h30m", 5400.0),
        ("1h2m3s", 3723.0),
        ("90s", 90.0),
    ],
)
def test_parse_duration(text, expected):
    assert parse_duration(text) == expected


def test_parse_duration_rejects_empty():
    with pytest.raises(ValueError):
        parse_duration("")


def test_parse_duration_rejects_junk():
    with pytest.raises(ValueError):
        parse_duration("forever")
