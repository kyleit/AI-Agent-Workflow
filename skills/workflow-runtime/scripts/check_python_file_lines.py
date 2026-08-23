#!/usr/bin/env python3
"""
FILE SIZE VALIDATION GATE

Enforces a maximum of 500 physical lines per Python source file.
Physical line = number of newline characters + 1 if file doesn't end in newline.

Usage:
    python scripts/check_python_file_lines.py [--max-lines N] [--path PATH]

Exit codes:
    0  All files pass (≤500 lines)
    1  One or more files exceed the limit

Exclusions:
    - __pycache__ directories
    - .agents/ directories
    - scratch/ directories
    - data/ directories
    - vendor/ directories (none in this project)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Default configuration
DEFAULT_MAX_LINES = 500
DEFAULT_SOURCE_ROOT = Path(__file__).parent.parent / "workflow_runtime"

# Directories to exclude from scanning
EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".agents",
    "scratch",
    "data",
    "artifacts",
    "vendor",
    ".venv",
    "venv",
    ".git",
}


def count_physical_lines(fpath: Path) -> int:
    """Count physical lines in a file.

    Uses newline count: a file with N newlines has N+1 lines
    unless the last char is a newline (N lines).
    This is the standard 'wc -l' definition.
    """
    content = fpath.read_bytes()
    if not content:
        return 0
    # Count \n characters (handles both LF and CRLF since CRLF has one \n per line)
    newlines = content.count(b"\n")
    # If file doesn't end with \n, the last line still counts
    if content[-1:] != b"\n":
        return newlines + 1
    return newlines


def is_excluded(fpath: Path) -> bool:
    """Return True if any part of the path matches an excluded directory."""
    return any(part in EXCLUDED_DIR_NAMES for part in fpath.parts)


def scan_python_files(source_root: Path) -> list[Path]:
    """Return all non-excluded Python files under source_root."""
    return sorted(
        f
        for f in source_root.rglob("*.py")
        if not is_excluded(f)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Python file line counts (max 500 physical lines).",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"Maximum physical lines per file (default: {DEFAULT_MAX_LINES})",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help=f"Source root to scan (default: {DEFAULT_SOURCE_ROOT})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print failures and summary",
    )
    args = parser.parse_args()

    max_lines: int = args.max_lines
    source_root: Path = args.path

    if not source_root.exists():
        print(f"ERROR: Source root does not exist: {source_root}", file=sys.stderr)
        return 2

    py_files = scan_python_files(source_root)
    violations: list[tuple[Path, int]] = []

    for fpath in py_files:
        try:
            line_count = count_physical_lines(fpath)
        except OSError as e:
            print(f"WARNING: Cannot read {fpath}: {e}", file=sys.stderr)
            continue

        if line_count > max_lines:
            violations.append((fpath, line_count))

    # --- Report ---
    print()
    print("FILE SIZE VALIDATION")
    print("=" * 60)
    print(f"Limit:   {max_lines} physical lines")
    print(f"Scanned: {len(py_files)} Python files")
    print()

    if violations:
        print("STATUS: FAIL")
        print()
        for fpath, line_count in sorted(violations, key=lambda x: -x[1]):
            exceeded = line_count - max_lines
            rel = fpath.relative_to(source_root.parent) if fpath.is_relative_to(source_root.parent) else fpath
            print(f"  FAIL  {rel}")
            print(f"        Lines: {line_count}  (exceeds limit by {exceeded})")
            print()
        print(f"{len(violations)} violation(s) found.")
        print()
        return 1

    # All passed
    print("STATUS: PASS")
    print()

    if not args.quiet:
        # Find and report the largest file
        file_sizes = []
        for fpath in py_files:
            try:
                file_sizes.append((count_physical_lines(fpath), fpath))
            except OSError:
                pass
        if file_sizes:
            largest_lines, largest_file = max(file_sizes)
            rel = largest_file.relative_to(source_root.parent) if largest_file.is_relative_to(source_root.parent) else largest_file
            print(f"Largest file: {rel}")
            print(f"Largest file lines: {largest_lines}")
            print()

    print(f"Violations: 0")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
