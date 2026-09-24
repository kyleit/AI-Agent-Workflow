#!/usr/bin/env python3
"""Validate implementation-ready block coverage across a Blueprint artifact set."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Sibling modules resolve by directory, and callers do not all insert it. The
# gate runner has always self-inserted; doing the same here keeps this module
# loadable under any loader, including a bare spec_from_file_location.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from block_contract import is_region_modify  # noqa: E402
from matrix_cells import (  # noqa: E402
    IGNORE_IDS as _IGNORE_IDS,
    MATRIX_HEADING as _MATRIX_HEADING,
    SCREEN_MATRIX_HEADING as _SCREEN_MATRIX_HEADING,
    SEPARATOR as _SEPARATOR,
    cell_is_not_applicable as _cell_is_not_applicable,
    cells as _cells,
    display_path as _display_path,
    find_column as _find_column,
    header_key as _header_key,
    ids as _ids,
    integer as _integer,
)
from validate_code_block_semantics import validate_code_block_semantics  # noqa: E402

# Initialization-only rules live in their own module, and are re-exported below so
# that existing callers and tests keep working. This import is the single direction
# of the dependency; that module must never import this one.
from validate_project_surface import (  # noqa: E402
    screen_route_findings,
    validate_greenfield_completeness_matrices,
    validate_project_initialization_surface,
)

# An existing test reaches for the pre-move private name. Keeping the alias means a
# relocation cannot break a caller that was never part of the public surface.
_screen_route_findings = screen_route_findings


_SOURCE_SUFFIXES = {
    ".go", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".svelte",
    ".vue", ".astro", ".css", ".scss", ".sql", ".html", ".htm", ".yaml",
    ".yml", ".json", ".toml", ".xml", ".sh", ".bash", ".zsh", ".ps1",
    ".psm1", ".psd1", ".py", ".java", ".kt", ".kts", ".rs", ".c", ".h",
    ".cc", ".cpp", ".cxx", ".hpp", ".php", ".rb", ".swift", ".dart",
    ".tf", ".tfvars", ".proto", ".graphql",
}
_STRICT_MATRIX_MARKERS = (
    "master blueprint",
    "feature coverage matrix",
    "project initialization coverage matrix",
    "screen and route coverage matrix",
    "backend capability coverage matrix",
)
_STRICT_ROW_FIELDS = ("owner", "imports", "exports", "exact signatures", "commands", "tests", "evidence")
_GENERATED_MANIFESTS = {
    "go.sum",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
}
_MAX_PHYSICAL_FILE_LINES = 500


def _intrinsic_line_floor(target: str, code: str) -> int:
    """Keep a full-file claim from passing by lowering the matrix estimate.

    This is a conservative complexity floor derived from observable constructs,
    not a fixed document-size target. It protects common integration files while
    leaving genuinely small manifests and leaf helpers free to stay small.
    """
    normalized = target.replace("\\", "/").lower()
    lowered = code.lower()
    if lowered.strip() == "" or normalized.endswith(tuple(_GENERATED_MANIFESTS)):
        return 0
    if normalized.endswith("_test.go") or normalized.endswith("_test.ts") or normalized.endswith(".test.ts"):
        return 35
    if normalized.endswith(".go"):
        if "database/sql" in lowered or "create table" in lowered or "sql.open" in lowered:
            return 80
        if "fiber" in lowered and re.search(r"\b(?:get|post|put|patch|delete)\s*\(", lowered):
            return 40
        if "ticker" in lowered or "goroutine" in lowered or "go func" in lowered:
            return 50
        if "context.withtimeout" in lowered or "retry" in lowered:
            return 45
        return 20
    if normalized.endswith(".svelte"):
        if "/views/" in normalized or "<form" in lowered or "on:submit" in lowered:
            return 45
        return 20
    if normalized.endswith((".ts", ".tsx", ".js", ".jsx", ".css", ".scss")):
        return 20
    if normalized.endswith((".html", ".htm", ".json", ".yaml", ".yml", ".toml", ".xml")):
        return 10
    return 0


def _path_matches(block_file: str, matrix_file: str) -> bool:
    block_path = block_file.replace("\\", "/").strip("`").strip()
    matrix_path = matrix_file.replace("\\", "/").strip("`").strip()
    return block_path == matrix_path or block_path.endswith("/" + matrix_path)


def extract_file_matrix_entries(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, str]] = []
    findings: list[str] = []
    for index, line in enumerate(lines[:-1]):
        if not _MATRIX_HEADING.match(line.strip()):
            continue
        table_index = index + 1
        while table_index < len(lines):
            candidate = lines[table_index].strip()
            if candidate.startswith("|"):
                break
            if candidate.startswith("#"):
                break
            table_index += 1
        if table_index + 1 >= len(lines) or not lines[table_index].lstrip().startswith("|"):
            findings.append(f"file_matrix_missing_table:{_display_path(path)}")
            continue
        headers = _cells(lines[table_index])
        if not _SEPARATOR.match(lines[table_index + 1]):
            findings.append(f"file_matrix_missing_separator:{_display_path(path)}")
            continue
        # Match the file column by normalized header, not substring search.
        # "Profile" contains the characters "file" and used to be selected
        # accidentally, making every valid row look like a profile path.
        file_column = next(
            (
                column
                for column, header in enumerate(headers)
                if _header_key(header)
                in {"path", "file", "file path", "target file", "relative file path"}
            ),
            None,
        )
        block_column = _find_column(headers, "code block", "implementation block", "block id")
        if file_column is None:
            findings.append(f"file_matrix_missing_file_column:{_display_path(path)}")
            continue
        if block_column is None:
            findings.append(f"file_matrix_missing_code_block_ids_column:{_display_path(path)}")
            continue
        row_index = table_index + 2
        while row_index < len(lines) and lines[row_index].lstrip().startswith("|"):
            row = _cells(lines[row_index])
            if len(row) > file_column:
                target = row[file_column].strip()
                if target and target not in {"-", "---"}:
                    projected_column = _find_column(headers, "projected lines", "lines")
                    block_cell = row[block_column] if len(row) > block_column else ""
                    entries.append(
                        {
                            "blueprint": str(path),
                            "file": target,
                            "code_block_ids": ",".join(_ids(block_cell)),
                            # plan-to-blueprint documents that a row may declare an
                            # explicit not-applicable reason instead of a block id,
                            # for a deliverable that is legitimately not source code.
                            "not_applicable": "true" if _cell_is_not_applicable(block_cell) else "",
                            "header_count": str(len(headers)),
                            "value_count": str(len(row)),
                            "projected_lines": str(
                                _integer(row[projected_column])
                                if projected_column is not None and len(row) > projected_column
                                else 0
                            ),
                            "row_values": row,
                            "headers": headers,
                        }
                    )
            row_index += 1
    if not entries and not findings:
        findings.append(f"file_matrix_missing:{_display_path(path)}")
    return entries, findings


def validate_artifact_set(
    artifact_paths: list[Path],
    discoveries: list[dict],
) -> list[str]:
    findings: list[str] = []
    entries: list[dict[str, str]] = []
    for path in artifact_paths:
        matrix_entries, matrix_findings = extract_file_matrix_entries(path)
        entries.extend(matrix_entries)
        findings.extend(matrix_findings)

    strict_contract = _is_strict_artifact_set(artifact_paths, entries)

    # A sizeable greenfield blueprint is an artifact set, not a single file.
    # Let the gate fail closed when the caller forgot to include the phase
    # artifacts; otherwise a thin master can pass while all implementation
    # detail is absent from the validated scope.
    if strict_contract and len(artifact_paths) == 1:
        findings.append("artifact_set_phase_blueprints_missing")

    blocks_by_id: dict[str, dict] = {}
    duplicate_ids: set[str] = set()
    for discovery in discoveries:
        for block in discovery.get("blocks", []):
            if not block.get("implementation_ready"):
                continue
            block_id = str(block.get("id", "")).strip()
            if block_id in blocks_by_id:
                duplicate_ids.add(block_id)
            blocks_by_id[block_id] = block
    findings.extend(f"duplicate_code_block_id:{block_id}" for block_id in sorted(duplicate_ids))

    matrix_files = {entry["file"].replace("\\", "/") for entry in entries}
    covered_files: set[str] = set()
    for entry in entries:
        target = entry["file"].replace("\\", "/")
        if _integer(entry.get("value_count", "0")) > _integer(entry.get("header_count", "0")):
            # More values than headers means the row was misread, and every column
            # after the break holds the wrong field. Name it instead of reporting
            # whichever field happened to land on a placeholder.
            findings.append(f"file_matrix_row_column_count_mismatch:{target}")
        block_ids = [item for item in entry["code_block_ids"].split(",") if item]
        if entry.get("not_applicable"):
            # A contradiction is decided structurally, never by guessing whether
            # the text after the marker is an identifier or a free-text reason:
            # the row says no source code applies, yet a real block targets it.
            if any(_path_matches(str(block.get("file", "")).replace("\\", "/"), target)
                   for block in blocks_by_id.values()):
                findings.append(f"file_matrix_contradictory_coverage:{target}")
                continue
            # The row declares a deliverable that is legitimately not source code:
            # retained evidence, a verification report, a handover note. It is
            # covered by its declaration, so no block is demanded.
            covered_files.add(target)
            continue
        if not block_ids:
            findings.append(f"file_matrix_row_missing_code_block:{target}")
            continue
        matching = []
        for block_id in block_ids:
            block = blocks_by_id.get(block_id)
            if block is None:
                findings.append(f"file_matrix_unknown_code_block:{target}:{block_id}")
                continue
            block_file = str(block.get("file", "")).replace("\\", "/")
            if not _path_matches(block_file, target):
                findings.append(f"code_block_file_mismatch:{block_id}:{block_file}!={target}")
            else:
                suffix = Path(block_file).suffix.lower()
                region_modify = is_region_modify(block)
                if suffix in _SOURCE_SUFFIXES and not region_modify:
                    generated_manifest = (
                        str(block.get("language", "")).strip().lower() == "generated-manifest"
                        and str(block.get("block_scope", "")).strip().lower() == "generated-manifest"
                        and str(block.get("operation", "")).strip().lower() == "generate"
                    )
                    if not generated_manifest and (
                        block.get("block_scope") != "full-file" or not block.get("full_file")
                    ):
                        findings.append(f"code_block_not_full_file:{block_id}:{block_file}")
                projected_lines = _integer(entry.get("projected_lines", "0"))
                code_lines = len(str(block.get("code", "")).splitlines())
                if (
                    strict_contract
                    and suffix in _SOURCE_SUFFIXES
                    and not region_modify
                    and Path(block_file).name.lower() not in _GENERATED_MANIFESTS
                ):
                    if projected_lines > _MAX_PHYSICAL_FILE_LINES:
                        findings.append(
                            f"physical_file_projected_lines_exceed_limit:{target}:{projected_lines}>{_MAX_PHYSICAL_FILE_LINES}"
                        )
                    if code_lines > _MAX_PHYSICAL_FILE_LINES:
                        findings.append(
                            f"physical_file_code_lines_exceed_limit:{block_id}:{block_file}:{code_lines}>{_MAX_PHYSICAL_FILE_LINES}"
                        )
                if strict_contract and suffix in _SOURCE_SUFFIXES and not projected_lines:
                    findings.append(f"file_matrix_missing_projected_lines:{target}")
                if strict_contract and suffix in _SOURCE_SUFFIXES and projected_lines and not region_modify:
                    # Projected lines are planning metadata, not a license to
                    # require filler. Full-file integrity is checked against
                    # the observable complexity floor and the 500-line limit.
                    # A region is sized by its region, so the floor cannot apply.
                    minimum_lines = max(1, _intrinsic_line_floor(block_file, str(block.get("code", ""))))
                    if code_lines < minimum_lines:
                        findings.append(
                            f"code_block_too_thin:{block_id}:{code_lines}<{minimum_lines}:{block_file}"
                        )
                matching.append(block_id)
        if matching:
            covered_files.add(target)
    for block_id, block in blocks_by_id.items():
        target = str(block.get("file", "")).replace("\\", "/")
        if target and target not in matrix_files:
            findings.append(f"code_block_target_missing_from_file_matrix:{block_id}:{target}")
    if not entries:
        findings.append("artifact_set_file_matrix_empty")
    if strict_contract:
        findings.extend(_strict_matrix_findings(entries))
        findings.extend(_hierarchy_findings(artifact_paths, entries))
        findings.extend(screen_route_findings(artifact_paths, blocks_by_id))
    findings.extend(validate_project_initialization_surface(artifact_paths, entries, blocks_by_id))
    findings.extend(validate_greenfield_completeness_matrices(artifact_paths))
    findings.extend(validate_code_block_semantics(discoveries))
    return sorted(set(findings))


def _is_strict_artifact_set(artifact_paths: list[Path], entries: list[dict[str, str]]) -> bool:
    """Recognize implementation plans that promise complete delivery.

    Small unit tests intentionally exercise the low-level mapping parser with
    tiny tables. Real master/phase blueprints and any sizeable file inventory
    must satisfy the stronger Superpowers-style task contract.
    """
    if len(entries) >= 4:
        return True
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in artifact_paths)
    return any(marker in text for marker in _STRICT_MATRIX_MARKERS)


def _strict_matrix_findings(entries: list[dict[str, str]]) -> list[str]:
    findings: list[str] = []
    for entry in entries:
        if entry.get("not_applicable"):
            # The row's deliverable is not source code, so a signature, an import
            # list, or a command for it would be fiction.
            continue
        target = entry["file"].replace("\\", "/")
        headers = entry.get("headers", [])
        values = entry.get("row_values", [])
        for field in _STRICT_ROW_FIELDS:
            column = _find_column(headers, field)
            value = values[column].strip() if column is not None and len(values) > column else ""
            suffix = Path(target).suffix.lower()
            operation = " ".join(values).lower()
            no_value_allowed = field in {"imports", "exports", "exact signatures"} and value.lower() in {
                "none", "n/a", "na"
            }
            generated_manifest = Path(target).name.lower() in _GENERATED_MANIFESTS or "generated" in operation
            if no_value_allowed and (
                field in {"imports", "exports", "exact signatures"}
                and (generated_manifest or field in {"exports", "exact signatures"} or suffix in {".woff", ".woff2", ".ttf", ".otf"})
            ):
                continue
            if not value or value.lower() in _IGNORE_IDS:
                findings.append(f"file_matrix_row_missing_{_header_key(field).replace(' ', '_')}:{target}")
    return findings


def _hierarchy_findings(
    artifact_paths: list[Path],
    entries: list[dict[str, str]],
) -> list[str]:
    """Require family directories for large master/phase artifact sets."""
    if len(artifact_paths) <= 1:
        return []
    master_text = artifact_paths[0].read_text(encoding="utf-8").lower()
    if "master blueprint" not in master_text and "greenfield" not in master_text:
        return []
    findings: list[str] = []
    if not _has_data_flow_sequence_heading(master_text):
        findings.append("master_data_flow_and_sequence_diagram_missing")
    root = artifact_paths[0].parent
    phase_paths = artifact_paths[1:]
    if any(len(path.relative_to(root).parts) < 2 for path in phase_paths):
        findings.append("phase_family_layout_required:phases_must_live_under_family_directories")
    family_counts: dict[str, int] = {}
    family_subfeatures: dict[str, set[str]] = {}
    for path in phase_paths:
        parts = path.relative_to(root).parts
        if len(parts) < 2:
            continue
        family = parts[0].lower()
        family_counts[family] = family_counts.get(family, 0) + 1
        if len(parts) >= 3:
            family_subfeatures.setdefault(family, set()).add(parts[1].lower())
    for family, count in family_counts.items():
        if count > 8 and not family_subfeatures.get(family):
            findings.append(f"phase_subfeature_layout_required:{family}:artifacts={count}")
    # Count the rows the extractor actually produced, grouped by the family that
    # declared them. The previous count came from a regular expression over whole
    # documents, which treated any table row whose third cell began with an
    # operation verb as a file, so a task contract inflated the count and forced a
    # directory layout by word choice.
    file_rows_by_family: dict[str, int] = {}
    for entry in entries:
        try:
            parts = Path(entry["blueprint"]).relative_to(root).parts
        except ValueError:
            continue
        if len(parts) < 2:
            continue
        family = parts[0].lower()
        file_rows_by_family[family] = file_rows_by_family.get(family, 0) + 1
    for family, count in file_rows_by_family.items():
        if count > 8 and not family_subfeatures.get(family):
            findings.append(f"phase_subfeature_layout_required:{family}:files={count}")
    return findings


def _has_data_flow_sequence_heading(text: str) -> bool:
    return bool(
        re.search(
            r"^#{1,6}\s+.*(?:data\s+flow.*sequence\s+diagram|sequence.*data\s+flow.*diagram)",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    )


__all__ = [
    "extract_file_matrix_entries",
    "validate_artifact_set",
    "validate_project_initialization_surface",
    "validate_greenfield_completeness_matrices",
]
