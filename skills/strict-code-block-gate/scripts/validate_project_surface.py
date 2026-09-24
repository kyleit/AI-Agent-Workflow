#!/usr/bin/env python3
"""Rules that apply only to a declared project initialization.

These obligations describe a product surface that a new project must deliver. They
used to be evaluated on every Blueprint, so a brownfield service document was asked
for user-interface control files because its prose happened to contain the words the
rules scan for: a contract table column name, a query keyword, a hash algorithm
beside a web router. None of that means the project is a new user interface.

They now run only when the master document declares the initialization in its front
matter. The obligations themselves are unchanged.

This module must not import the coverage validator. The coverage validator imports
this one, and keeping the arrow pointing in a single direction is what prevents a
cycle.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Sibling modules resolve by directory, and callers do not all insert it.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from matrix_cells import (  # noqa: E402
    SCREEN_MATRIX_HEADING as _SCREEN_MATRIX_HEADING,
    SEPARATOR as _SEPARATOR,
    cells as _cells,
    display_path as _display_path,
    find_column as _find_column,
    ids as _ids,
)

_INITIALIZATION_DECLARED = re.compile(
    r"^project_initialization:\s*true\s*$", re.IGNORECASE | re.MULTILINE
)


def initialization_declared(artifact_paths: list[Path]) -> bool:
    """Read the declaration from the master document, not from prose.

    A document that discusses initialization, quotes this module, or documents the
    declaration is not itself an initialization. Only the declaration counts.
    """
    if not artifact_paths:
        return False
    try:
        master = artifact_paths[0].read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return bool(_INITIALIZATION_DECLARED.search(master))


def validate_project_initialization_surface(
    artifact_paths: list[Path],
    entries: list[dict[str, str]],
    blocks_by_id: dict[str, dict],
) -> list[str]:
    """Catch common greenfield omissions hidden by a high-level capability row."""
    if not initialization_declared(artifact_paths):
        return []
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in artifact_paths)
    files = {entry["file"].replace("\\", "/").lower() for entry in entries}
    requirements: list[tuple[str, bool]] = [
        ("radio_control", "radio" in text),
        ("textarea_control", "textarea" in text),
        ("input_control", "input" in text),
        ("select_control", "select" in text),
        ("checkbox_control", "checkbox" in text),
        ("dialog_host", "alert" in text and "prompt" in text and "confirm" in text),
        ("hash_router", "hash" in text and "router" in text),
        ("tailwind_config", "tailwind" in text),
        ("fiber_routes", "fiber" in text),
        ("sqlite_migration", "sqlite" in text),
        ("wails_config", "wails" in text),
        ("systray", "systray" in text or "tray" in text),
        ("loading_component", "loading" in text or "skeleton" in text),
        ("local_font_assets", "font" in text and "local" in text),
        ("frontend_entrypoint", "svelte" in text and "spa" in text),
    ]
    expected_patterns = {
        "radio_control": ("/radio", "radio."),
        "textarea_control": ("/textarea", "textarea."),
        "input_control": ("/input", "input."),
        "select_control": ("/select", "select."),
        "checkbox_control": ("/checkbox", "checkbox."),
        "dialog_host": ("dialog",),
        "hash_router": ("router",),
        "tailwind_config": ("tailwind.config",),
        "fiber_routes": ("routes", "handlers"),
        "sqlite_migration": (".sql", "migration"),
        "wails_config": ("wails.json",),
        "systray": ("systray", "tray"),
        "loading_component": ("loading", "skeleton", "spinner"),
        "local_font_assets": (".woff2", ".woff", ".ttf", ".otf"),
        "frontend_entrypoint": ("frontend/src/main.", "frontend/index.html"),
    }
    findings = []
    for requirement, enabled in requirements:
        if not enabled:
            continue
        patterns = expected_patterns[requirement]
        if not any(any(pattern in file for pattern in patterns) for file in files):
            findings.append(f"project_init_required_surface_missing:{requirement}")
    if "go.mod" in files and "go.sum" not in files:
        findings.append("project_init_required_surface_missing:go_dependency_lock")
    if "frontend/package.json" in files:
        for required in ("frontend/index.html", "frontend/tsconfig.json"):
            if required not in files:
                findings.append(f"project_init_required_surface_missing:{required}")
    if "frontend/tailwind.config.cjs" in files and "frontend/postcss.config.cjs" not in files:
        findings.append("project_init_required_surface_missing:frontend/postcss.config.cjs")
    return findings


def validate_greenfield_completeness_matrices(artifact_paths: list[Path]) -> list[str]:
    """Require explicit capability, screen, contract, test, and viewport maps."""
    if not initialization_declared(artifact_paths):
        return []
    combined = "\n".join(path.read_text(encoding="utf-8") for path in artifact_paths)
    lowered = combined.lower()

    required: list[tuple[str, tuple[str, ...]]] = [
        (
            "Greenfield Completeness Matrix",
            ("surface", "required files", "code block", "producer", "consumer", "test", "evidence"),
        ),
        (
            "Test Scenario Coverage Matrix",
            ("test", "entrypoint", "assertion", "command", "evidence"),
        ),
    ]
    if any(token in lowered for token in ("svelte", "frontend", "route", "screen")):
        required.extend(
            [
                ("Screen And Route Coverage Matrix", ("route", "screen", "concrete files", "code blocks")),
                ("Mobile-First Visual Coverage Matrix", ("mobile", "desktop", "tablet", "state", "evidence")),
            ]
        )
    if any(token in lowered for token in ("fiber", "api", "backend", "sqlite")):
        required.append(
            (
                "Backend Capability Coverage Matrix",
                ("capability", "endpoint", "persistence", "consumer", "test", "evidence"),
            )
        )

    findings: list[str] = []
    for heading, required_terms in required:
        heading_match = re.search(
            rf"^#{{1,6}}\s+.*{re.escape(heading)}.*$",
            combined,
            re.IGNORECASE | re.MULTILINE,
        )
        if not heading_match:
            findings.append(f"greenfield_required_matrix_missing:{heading}")
            continue
        next_heading = re.search(r"^#{1,6}\s+", combined[heading_match.end():], re.MULTILINE)
        section_end = heading_match.end() + (next_heading.start() if next_heading else 4000)
        section = combined[heading_match.end():section_end].lower()
        if "|" not in section:
            findings.append(f"greenfield_required_matrix_table_missing:{heading}")
            continue
        for term in required_terms:
            if term.lower() not in section:
                findings.append(f"greenfield_required_matrix_column_missing:{heading}:{term}")
    return findings

def _extract_screen_route_contracts(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    """Extract route rows so declared UI surfaces have concrete implementations."""
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, object]] = []
    findings: list[str] = []
    for index, line in enumerate(lines[:-1]):
        if not _SCREEN_MATRIX_HEADING.match(line.strip()):
            continue
        table_index = index + 1
        while table_index < len(lines) and not lines[table_index].lstrip().startswith("|"):
            if lines[table_index].lstrip().startswith("#"):
                break
            table_index += 1
        if table_index + 1 >= len(lines) or not lines[table_index].lstrip().startswith("|"):
            findings.append(f"screen_route_matrix_missing_table:{_display_path(path)}")
            continue
        headers = _cells(lines[table_index])
        if not _SEPARATOR.match(lines[table_index + 1]):
            findings.append(f"screen_route_matrix_missing_separator:{_display_path(path)}")
            continue
        route_column = _find_column(headers, "route", "path", "url")
        screen_column = _find_column(headers, "screen", "view", "page")
        files_column = _find_column(headers, "concrete files", "files", "implementation file")
        blocks_column = _find_column(headers, "code blocks", "code block", "implementation block")
        if route_column is None or screen_column is None or files_column is None or blocks_column is None:
            findings.append(f"screen_route_matrix_missing_required_columns:{_display_path(path)}")
            continue
        row_index = table_index + 2
        while row_index < len(lines) and lines[row_index].lstrip().startswith("|"):
            row = _cells(lines[row_index])
            required = max(route_column, screen_column, files_column, blocks_column)
            if len(row) > required:
                route = row[route_column].strip().strip("`")
                screen = row[screen_column].strip()
                files = [
                    item.strip()
                    for item in re.findall(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.*-]+", row[files_column])
                ]
                block_ids = _ids(row[blocks_column])
                if route and screen and route not in {"-", "---"} and route.startswith(("#", "/")):
                    entries.append({"route": route, "screen": screen, "files": files, "code_block_ids": block_ids})
            row_index += 1
    return entries, findings


def screen_route_findings(
    artifact_paths: list[Path],
    blocks_by_id: dict[str, dict],
) -> list[str]:
    """Reject multi-route SPAs whose coverage table hides screens in one shell."""
    contracts: list[dict[str, object]] = []
    findings: list[str] = []
    for path in artifact_paths:
        discovered, discovered_findings = _extract_screen_route_contracts(path)
        contracts.extend(discovered)
        findings.extend(discovered_findings)
    if len(contracts) < 3:
        return findings

    covered_files = {
        str(block.get("file", "")).replace("\\", "/").lower()
        for block in blocks_by_id.values()
        if block.get("file")
    }
    for contract in contracts:
        route = str(contract["route"])
        files = [str(item).replace("\\", "/") for item in contract["files"]]
        block_ids = [str(item) for item in contract["code_block_ids"]]
        if not files:
            findings.append(f"screen_route_concrete_file_missing:{route}")
            continue
        if len(files) == 1 and files[0].lower().endswith("/app.svelte") and route not in {"#", "#/", "/"}:
            findings.append(f"screen_route_shared_app_shell_for_feature_route:{route}:{files[0]}")
        for target in files:
            if target.lower() not in covered_files:
                findings.append(f"screen_route_file_not_covered:{route}:{target}")
        if not block_ids:
            findings.append(f"screen_route_missing_code_block_ids:{route}")
        covered_targets = {
            str(blocks_by_id[block_id].get("file", "")).replace("\\", "/").lower()
            for block_id in block_ids
            if block_id in blocks_by_id
        }
        for block_id in block_ids:
            if block_id not in blocks_by_id:
                findings.append(f"screen_route_unknown_code_block:{route}:{block_id}")
        for target in files:
            if target.lower() not in covered_targets:
                findings.append(f"screen_route_code_block_file_mismatch:{route}:{target}")
    return findings


__all__ = [
    "initialization_declared",
    "screen_route_findings",
    "validate_greenfield_completeness_matrices",
    "validate_project_initialization_surface",
]
