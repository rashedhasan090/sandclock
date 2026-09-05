from pathlib import Path

from sandclock.fsdelta import diff, snapshot


def test_snapshot_diff_create_modify_delete(tmp_path: Path):
    root = tmp_path
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    (root / "keep.txt").write_text("same\n", encoding="utf-8")
    before = snapshot(root, hash_bytes=10_000)

    (root / "b.txt").write_text("new\n", encoding="utf-8")
    (root / "a.txt").write_text("two\n", encoding="utf-8")
    (root / "keep.txt").write_text("same\n", encoding="utf-8")
    (root / "gone.txt").write_text("bye\n", encoding="utf-8")
    # delete gone after including it in a mid snapshot isn't needed;
    # instead delete a file that existed in before
    (root / "a.txt").write_text("two\n", encoding="utf-8")

    # recreate scenario cleanly:
    # before had a.txt + keep.txt
    # after: keep.txt same, a.txt modified, b.txt created, and we delete nothing from before except we add deletion of a dedicated file
    (root / "delete_me.txt").write_text("x\n", encoding="utf-8")
    before = snapshot(root, hash_bytes=10_000)
    (root / "b2.txt").write_text("created\n", encoding="utf-8")
    (root / "a.txt").write_text("changed\n", encoding="utf-8")
    (root / "delete_me.txt").unlink()
    after = snapshot(root, hash_bytes=10_000)
    delta = diff(before, after)

    assert "b2.txt" in delta.created
    assert "a.txt" in delta.modified
    assert "delete_me.txt" in delta.deleted
    assert "keep.txt" not in delta.modified


def test_ignore_venv_style_dirs(tmp_path: Path):
    (tmp_path / "tracked.txt").write_text("ok\n", encoding="utf-8")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "noise.py").write_text("nope\n", encoding="utf-8")
    snap = snapshot(tmp_path)
    assert "tracked.txt" in snap
    assert not any(k.startswith(".venv/") for k in snap)
