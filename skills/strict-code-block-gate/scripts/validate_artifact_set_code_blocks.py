#!/usr/bin/env python3
"""Validate implementation-ready block coverage across a Blueprint artifact set."""

from __future__ import annotations

import re
from pathlib import Path

from validate_code_block_semantics import validate_code_block_semantics


_MATRIX_HEADING = re.compile(r"^#{1,6}\s+.*file[- ]by[- ]file change matrix", re.IGNORECASE)
_SCREEN_MATRIX_HEADING = re.compile(
    r"^#{1,6}\s+.*(?:screen\s+and\s+route|route\s+and\s+screen|screen\s+coverage).*?$",
    re.IGNORECASE,
)
_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")
_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")
_IGNORE_IDS = {"none", "n/a", "na", "tbd", "todo", "-"}
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


def _cells(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip().strip("`") for cell in value.split("|")]


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _find_column(headers: list[str], *needles: str) -> int | None:
    for index, header in enumerate(headers):
        key = _header_key(header)
        if any(needle in key for needle in needles):
            return index
    return None


def _ids(value: str) -> list[str]:
    return [item for item in _ID_RE.findall(value) if item.lower() not in _IGNORE_IDS]


def _integer(value: str) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


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
            findings.append(f"file_matrix_missing_table:{path}")
            continue
        headers = _cells(lines[table_index])
        if not _SEPARATOR.match(lines[table_index + 1]):
            findings.append(f"file_matrix_missing_separator:{path}")
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
            findings.append(f"file_matrix_missing_file_column:{path}")
            continue
        if block_column is None:
            findings.append(f"file_matrix_missing_code_block_ids_column:{path}")
            continue
        row_index = table_index + 2
        while row_index < len(lines) and lines[row_index].lstrip().startswith("|"):
            row = _cells(lines[row_index])
            if len(row) > file_column:
                target = row[file_column].strip()
                if target and target not in {"-", "---"}:
                    projected_column = _find_column(headers, "projected lines", "lines")
                    entries.append(
                        {
                            "blueprint": str(path),
                            "file": target,
                            "code_block_ids": ",".join(
                                _ids(row[block_column]) if len(row) > block_column else []
                            ),
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
        findings.append(f"file_matrix_missing:{path}")
    return entries, findings


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
            findings.append(f"screen_route_matrix_missing_table:{path}")
            continue
        headers = _cells(lines[table_index])
        if not _SEPARATOR.match(lines[table_index + 1]):
            findings.append(f"screen_route_matrix_missing_separator:{path}")
            continue
        route_column = _find_column(headers, "route", "path", "url")
        screen_column = _find_column(headers, "screen", "view", "page")
        files_column = _find_column(headers, "concrete files", "files", "implementation file")
        blocks_column = _find_column(headers, "code blocks", "code block", "implementation block")
        if route_column is None or screen_column is None or files_column is None or blocks_column is None:
            findings.append(f"screen_route_matrix_missing_required_columns:{path}")
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


def _screen_route_findings(
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
        block_ids = [item for item in entry["code_block_ids"].split(",") if item]
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
                if suffix in _SOURCE_SUFFIXES:
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
                if strict_contract and suffix in _SOURCE_SUFFIXES and projected_lines:
                    # Projected lines are planning metadata, not a license to
                    # require filler. Full-file integrity is checked against
                    # the observable complexity floor and the 500-line limit.
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
        findings.extend(_hierarchy_findings(artifact_paths))
        findings.extend(_screen_route_findings(artifact_paths, blocks_by_id))
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


def _hierarchy_findings(artifact_paths: list[Path]) -> list[str]:
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
    file_rows_by_family: dict[str, int] = {}
    for path in phase_paths:
        family = path.relative_to(root).parts[0].lower()
        text = path.read_text(encoding="utf-8")
        file_rows_by_family[family] = file_rows_by_family.get(family, 0) + len(
            re.findall(
                r"^\|\s*[^|]+\|[^|]+\|\s*(?:NEW|MODIFY|DELETE|REPLACE|CREATE|ADD)",
                text,
                re.IGNORECASE | re.MULTILINE,
            )
        )
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


def validate_project_initialization_surface(
    artifact_paths: list[Path],
    entries: list[dict[str, str]],
    blocks_by_id: dict[str, dict],
) -> list[str]:
    """Catch common greenfield omissions hidden by a high-level capability row."""
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
    master = artifact_paths[0].read_text(encoding="utf-8")
    lowered = master.lower()
    if "project_initialization: true" not in lowered:
        return []

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

    combined = "\n".join(path.read_text(encoding="utf-8") for path in artifact_paths)
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


__all__ = [
    "extract_file_matrix_entries",
    "validate_artifact_set",
    "validate_project_initialization_surface",
    "validate_greenfield_completeness_matrices",
]
