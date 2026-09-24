"""Prove discovery honours CommonMark fences longer than three backticks.

A Markdown file written as a full-file block must embed its own ``` fences, so
the block opens with four backticks. Closing on the first embedded ``` line
split it into a truncated block plus a phantom block made of the remainder.
"""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FENCE3 = "`" * 3
FENCE4 = "`" * 4


def _discover():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("discover_code_blocks", SCRIPTS / "discover_code_blocks.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.discover


def _write(tmp_path: Path, body: list[str]) -> Path:
    path = tmp_path / "blueprint.md"
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


_EMBEDDED = [
    "# Config reference",
    "",
    f"{FENCE3}json",
    '{"enabled": true}',
    FENCE3,
    "",
    "Trailing prose that belongs to the same file.",
]


def test_four_backtick_block_embedding_json_fence_is_one_block(tmp_path: Path) -> None:
    blueprint = _write(
        tmp_path,
        [
            "id: B01",
            "language: markdown",
            "file: docs/reference.md",
            "operation: create",
            "implementation_ready: true",
            "",
            f"{FENCE4}markdown",
            *_EMBEDDED,
            FENCE4,
            "",
            "Closing prose.",
        ],
    )

    blocks = _discover()(blueprint)["blocks"]

    assert len(blocks) == 1
    block = blocks[0]
    assert block["id"] == "B01"
    assert block["language"] == "markdown"
    assert block["code"] == "\n".join(_EMBEDDED) + "\n"
    assert block["start_line"] == 8
    assert block["end_line"] == 8 + len(_EMBEDDED)


def test_shorter_or_annotated_fence_does_not_close_a_longer_block(tmp_path: Path) -> None:
    inner = [FENCE3, f"{FENCE3}python", "x = 1", FENCE3]
    blueprint = _write(tmp_path, [f"{FENCE4}text", *inner, FENCE4])

    blocks = _discover()(blueprint)["blocks"]

    assert len(blocks) == 1
    assert blocks[0]["code"] == "\n".join(inner) + "\n"


def test_longer_bare_fence_closes_and_three_backtick_blocks_still_split(tmp_path: Path) -> None:
    blueprint = _write(
        tmp_path,
        [f"{FENCE3}python", "a = 1", "`" * 5, "", f"{FENCE3}go", "package main", FENCE3],
    )

    blocks = _discover()(blueprint)["blocks"]

    assert [block["language"] for block in blocks] == ["python", "go"]
    assert blocks[0]["code"] == "a = 1\n"
    assert blocks[1]["code"] == "package main\n"
