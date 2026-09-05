import json
import sys
from pathlib import Path

from sandclock.cli import main


def test_cli_json_delta(tmp_path: Path, capsys):
    code = main(
        [
            "5s",
            "--cwd",
            str(tmp_path),
            "--json",
            "--",
            sys.executable,
            "-c",
            "open('out.txt','w').write('hi')",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["timed_out"] is False
    assert "out.txt" in payload["created"]


def test_cli_timeout(tmp_path: Path, capsys):
    code = main(
        [
            "1s",
            "--cwd",
            str(tmp_path),
            "--json",
            "--",
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        ]
    )
    assert code == 124
    payload = json.loads(capsys.readouterr().out)
    assert payload["timed_out"] is True
