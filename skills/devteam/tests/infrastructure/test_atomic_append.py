import os

from devteam.infrastructure.fs.atomic import append_line, atomic_write


def test_append_line_adds_newline(tmp_path):
    p = os.path.join(str(tmp_path), "f.jsonl")
    append_line(p, "a")
    append_line(p, "b\n")
    assert open(p, encoding="utf-8").read() == "a\nb\n"


def test_atomic_write_replaces(tmp_path):
    p = os.path.join(str(tmp_path), "f.txt")
    atomic_write(p, "one")
    atomic_write(p, "two")
    assert open(p, encoding="utf-8").read() == "two"


def test_atomic_write_creates_dirs(tmp_path):
    p = os.path.join(str(tmp_path), "deep", "nested", "f.txt")
    atomic_write(p, "x")
    assert open(p, encoding="utf-8").read() == "x"
