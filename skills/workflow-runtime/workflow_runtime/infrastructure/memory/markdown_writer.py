from __future__ import annotations

import os
from datetime import datetime
from typing import Any, cast

# markdown_writer.py


def generate_project_summary(info: dict[str, Any]) -> str:
    raw_langs = info.get("languages")
    langs: list[str] = [str(x) for x in cast(list[Any], raw_langs)] if isinstance(raw_langs, list) and raw_langs else ["Unknown"]
    primary_lang = langs[0] if langs else "Unknown"
    secondary_langs = langs[1:] if len(langs) > 1 else []

    raw_modules = info.get("modules")
    modules: list[dict[str, Any]] = [cast(dict[str, Any], m) for m in cast(list[Any], raw_modules) if isinstance(m, dict)] if isinstance(raw_modules, list) else []
    modules_str = ""
    for mod in modules:
        mod_name = str(mod.get("name", ""))
        mod_path = str(mod.get("path", ""))
        mod_purpose = str(mod.get("purpose", ""))
        mod_details = str(mod.get("details", ""))
        modules_str += f"- **{mod_name}** (`{mod_path}`): {mod_purpose} {mod_details}\n"

    raw_dbs = info.get("databases")
    databases: list[dict[str, Any]] = [cast(dict[str, Any], db) for db in cast(list[Any], raw_dbs) if isinstance(db, dict)] if isinstance(raw_dbs, list) else []
    db_str = ""
    for db in databases:
        db_type = str(db.get("type", ""))
        db_path = str(db.get("path", ""))
        db_purpose = str(db.get("purpose", ""))
        db_str += f"- **{db_type}** (`{db_path}`): {db_purpose}\n"

    raw_infra = info.get("infrastructure")
    infrastructure: list[dict[str, Any]] = [cast(dict[str, Any], inf) for inf in cast(list[Any], raw_infra) if isinstance(inf, dict)] if isinstance(raw_infra, list) else []
    infra_str = ""
    for infra in infrastructure:
        inf_type = str(infra.get("type", ""))
        inf_purpose = str(infra.get("purpose", ""))
        inf_details = str(infra.get("details", ""))
        infra_str += f"- **{inf_type}**: {inf_purpose}. {inf_details}\n"

    raw_cmds = info.get("build_commands")
    build_commands: list[dict[str, Any]] = [cast(dict[str, Any], cmd) for cmd in cast(list[Any], raw_cmds) if isinstance(cmd, dict)] if isinstance(raw_cmds, list) else []
    build_str = ""
    for cmd in build_commands:
        cmd_str = str(cmd.get("command", ""))
        cmd_name = str(cmd.get("name", ""))
        build_str += f"- `{cmd_str}` ({cmd_name})\n"

    proj_name = str(info.get("project_name", os.path.basename(os.getcwd()) or "Unknown Project"))
    proj_desc = str(info.get("description", "A software project."))

    raw_frameworks = info.get("frameworks")
    frameworks: list[str] = [str(x) for x in cast(list[Any], raw_frameworks)] if isinstance(raw_frameworks, list) and raw_frameworks else ["None"]

    sec_langs_str = ", ".join(secondary_langs) if secondary_langs else "- None"
    frameworks_str = ", ".join(frameworks)

    md = f"""# Project Summary

## Project Name
{proj_name}

## Business Domain & Purpose
{proj_desc}

## Primary Language
{primary_lang}

## Secondary Languages
{sec_langs_str}

## Frameworks & Libraries
{frameworks_str}

## Architecture Style
To be documented.

## Main Modules
{modules_str if modules_str else "- None"}

## Databases & Storage Backends
{db_str if db_str else "- None"}

## Local Infrastructure & Models
{infra_str if infra_str else "- None"}

## External Services & Integrations
To be documented.

## Build Commands
{build_str if build_str else "- None"}

## Test/Verification Commands
To be documented.

## Deployment Method
To be documented.

## Coding Conventions
- Markdown files must follow GitHub-Flavored Markdown.
- Every skill folder must contain a `SKILL.md` with standard YAML frontmatter.
- Shell scripts must use standard environment paths and handle cross-platform compatibility.

## Naming Conventions
- Skill directories: kebab-case.
- Artifacts: `FEAT-XXX_slug.md` or `FIX-XXX_slug.md`.

## Known Anti-Patterns to Avoid
- Storing absolute file system paths in markdown files (always use relative paths).
- Over-scanning the entire repository during planning or brainstorming (always consult memory first).

## Memory Generated At
{datetime.now().strftime("%Y-%m-%d")}

## Memory Version
1.0.0
"""
    return md


def write_project_summary(dest_path: str, info: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    content = generate_project_summary(info)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_architecture_overview(dest_path: str, info: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    raw_langs = info.get("languages")
    langs: list[str] = [str(x) for x in cast(list[Any], raw_langs)] if isinstance(raw_langs, list) and raw_langs else ["Unknown"]
    primary_lang = langs[0] if langs else "Unknown"

    raw_frameworks = info.get("frameworks")
    frameworks: list[str] = [str(x) for x in cast(list[Any], raw_frameworks)] if isinstance(raw_frameworks, list) else []
    frameworks_str = ", ".join(frameworks) if frameworks else "None"

    raw_infra = info.get("infrastructure")
    infrastructure: list[dict[str, Any]] = [cast(dict[str, Any], inf) for inf in cast(list[Any], raw_infra) if isinstance(inf, dict)] if isinstance(raw_infra, list) else []
    infra_types = [str(inf.get("type", "")) for inf in infrastructure]
    infra_str = ", ".join(infra_types) if infra_types else "Chưa phát hiện"

    content = f"""# Architecture Overview

## Structural Overview
Tài liệu tổng quan kiến trúc dự án (Đang cập nhật...).

## Technology Stack
- **Ngôn ngữ chính**: {primary_lang}
- **Frameworks**: {frameworks_str}
- **Hạ tầng/Môi trường**: {infra_str}
"""
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)


__all__ = [
    "generate_project_summary",
    "write_project_summary",
    "write_architecture_overview",
]
