from __future__ import annotations

import os
from datetime import datetime
from typing import Any, cast

from .common import write_text_safe


def generate_project_summary(info: dict[str, Any], ai_synth: dict[str, Any] | None = None) -> str:
    raw_langs = info.get("languages")
    langs: list[str] = [str(x) for x in cast(list[Any], raw_langs)] if isinstance(raw_langs, list) and raw_langs else ["Python"]
    primary_lang = langs[0] if langs else "Python"
    secondary_langs = langs[1:] if len(langs) > 1 else []

    proj_name = str(info.get("project_name", os.path.basename(os.getcwd()) or "software-project"))

    if ai_synth and ai_synth.get("business_purpose"):
        proj_desc = str(ai_synth["business_purpose"])
    else:
        proj_desc = str(info.get("description", f"Software project for {proj_name}."))

    if ai_synth and ai_synth.get("architecture_style"):
        arch_style = str(ai_synth["architecture_style"])
    else:
        arch_style = f"Modular Multi-Tier Architecture in {primary_lang}"

    raw_modules = info.get("modules")
    modules: list[dict[str, Any]] = [cast(dict[str, Any], m) for m in cast(list[Any], raw_modules) if isinstance(m, dict)] if isinstance(raw_modules, list) else []
    modules_str = ""
    for mod in modules:
        mod_name = str(mod.get("name", ""))
        mod_path = str(mod.get("path", ""))
        mod_purpose = str(mod.get("purpose", ""))
        mod_details = str(mod.get("details", ""))
        modules_str += f"- **{mod_name}** (`{mod_path}`): {mod_purpose} ({mod_details})\n"

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
        infra_str += f"- **{inf_type}**: {inf_purpose} ({inf_details})\n"

    raw_cmds = info.get("build_commands")
    build_commands: list[dict[str, Any]] = [cast(dict[str, Any], cmd) for cmd in cast(list[Any], raw_cmds) if isinstance(cmd, dict)] if isinstance(raw_cmds, list) else []
    build_str = ""
    test_str = ""
    for cmd in build_commands:
        cmd_str = str(cmd.get("command", ""))
        cmd_name = str(cmd.get("name", ""))
        if "test" in cmd_name.lower() or "test" in cmd_str.lower():
            test_str += f"- `{cmd_str}` ({cmd_name})\n"
        else:
            build_str += f"- `{cmd_str}` ({cmd_name})\n"

    if not build_str:
        if primary_lang == "Go":
            build_str = "- `go build ./...` (Build all Go packages)\n"
        elif primary_lang in ("TypeScript", "JavaScript"):
            build_str = "- `npm run build` (Compile frontend/backend bundles)\n"
        elif primary_lang == "Python":
            build_str = "- `python -m build` (Build wheel and sdist)\n"
        elif primary_lang == "Rust":
            build_str = "- `cargo build --release` (Compile binary)\n"
        else:
            build_str = f"- Build with standard {primary_lang} toolchain\n"

    if not test_str:
        if primary_lang == "Go":
            test_str = "- `go test -v ./...` (Run full Go test suite)\n"
        elif primary_lang in ("TypeScript", "JavaScript"):
            test_str = "- `npm test` (Run unit and integration tests)\n"
        elif primary_lang == "Python":
            test_str = "- `pytest` (Run test suite)\n"
        elif primary_lang == "Rust":
            test_str = "- `cargo test` (Run test suite)\n"
        else:
            test_str = f"- Run tests with standard {primary_lang} test runner\n"

    raw_frameworks = info.get("frameworks")
    frameworks: list[str] = [str(x) for x in cast(list[Any], raw_frameworks)] if isinstance(raw_frameworks, list) and raw_frameworks else [primary_lang]

    sec_langs_str = ", ".join(secondary_langs) if secondary_langs else "None"
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
{arch_style}

## Main Subsystems & Modules
{modules_str if modules_str else "- None"}

## Databases & Storage Backends
{db_str if db_str else "- In-memory state or file-based storage"}

## Local Infrastructure & Services
{infra_str if infra_str else "- Standard runtime environment"}

## Build Commands
{build_str.strip()}

## Test / Verification Commands
{test_str.strip()}

## Coding & Architectural Conventions
- Follow standard idiomatic patterns for {primary_lang}.
- Keep subsystem boundaries modular with well-defined interfaces.
- Use explicit error propagation and avoid silent failures.

## Memory Generated At
{datetime.now().strftime("%Y-%m-%d")}

## Memory Version
2.1.0
"""
    return md


def write_project_summary(dest_path: str, info: dict[str, Any], ai_synth: dict[str, Any] | None = None) -> None:
    content = generate_project_summary(info, ai_synth)
    write_text_safe(dest_path, content)


def write_architecture_overview(dest_path: str, info: dict[str, Any], ai_synth: dict[str, Any] | None = None) -> None:
    fence = chr(96) * 3
    proj_name = str(info.get("project_name", "System"))
    primary_lang = str(info.get("languages", ["Application"])[0])

    if ai_synth and ai_synth.get("system_context"):
        sys_context = str(ai_synth["system_context"])
    else:
        sys_context = f"{proj_name} is organized as a modular {primary_lang} application coordinating client requests, business use-cases, and persistent storage."

    raw_modules = info.get("modules", [])
    modules = cast(list[dict[str, Any]], raw_modules) if isinstance(raw_modules, list) else []

    mermaid_nodes = ""
    if modules:
        top_mods = modules[:5]
        mermaid_nodes = f"    Client([Client / User]) --> Router[Gateway / Main Router]\n"
        for i, m in enumerate(top_mods):
            m_id = f"Mod{i}"
            m_name = m.get("name", f"Module {i}")
            mermaid_nodes += f"    Router --> {m_id}[{m_name}]\n"
        mermaid_nodes += f"    {f'Mod{len(top_mods)-1}'} --> Storage[(Data / Storage Backends)]"
    else:
        mermaid_nodes = f"""    Client([Client / User Request]) --> Router[Router / Controller]
    Router --> Service[Core Services]
    Service --> Storage[(Persistent Storage)]"""

    content = f"""# Architecture Overview

## System Context & Core Topology
{sys_context}

{fence}mermaid
graph TD
{mermaid_nodes}
{fence}

## High-Level Architectural Layers
1. **Entrypoint & Routing Layer**: Public interfaces, HTTP routes, CLI command handlers, and request parsers.
2. **Core Domain / Business Layer**: Domain entities, translation logic, algorithms, and orchestration services.
3. **Infrastructure & Persistence Layer**: Database adapters, external API clients, file storage, and network connectors.
"""
    write_text_safe(dest_path, content)


def write_architecture_components(dest_path: str, info: dict[str, Any], ai_synth: dict[str, Any] | None = None) -> None:
    raw_modules = info.get("modules", [])
    modules = cast(list[dict[str, Any]], raw_modules) if isinstance(raw_modules, list) else []

    ai_subsystems: dict[str, str] = {}
    if ai_synth and isinstance(ai_synth.get("core_subsystems"), list):
        for sub in ai_synth["core_subsystems"]:
            if isinstance(sub, dict) and "path" in sub:
                ai_subsystems[sub["path"]] = sub.get("purpose", "")

    lines = [
        "# Subsystem & Component Catalog",
        "",
        "This catalog documents the core components and subsystem boundaries for this project.",
        ""
    ]
    for m in modules:
        m_path = str(m.get("path", ""))
        purpose = ai_subsystems.get(m_path, m.get("purpose", ""))
        lines.append(f"## {m.get('name')}")
        lines.append(f"- **Path**: `{m_path}`")
        lines.append(f"- **Purpose**: {purpose}")
        lines.append(f"- **Details**: {m.get('details')}")
        lines.append("")

    write_text_safe(dest_path, "\n".join(lines) + "\n")


def write_architecture_data_flows(dest_path: str, ai_synth: dict[str, Any] | None = None) -> None:
    fence = chr(96) * 3
    if ai_synth and ai_synth.get("data_flow_description"):
        flow_desc = str(ai_synth["data_flow_description"])
    else:
        flow_desc = "Standard request execution lifecycle through entrypoint routing, domain processing, and persistence adapters."

    content = f"""# System Data Flows

## Overview
{flow_desc}

## Execution Lifecycle
{fence}mermaid
sequenceDiagram
    autonumber
    actor Client as Client / User
    participant Router as Entrypoint / Router
    participant Core as Core Logic / Handlers
    participant Store as Storage / External APIs

    Client->>Router: Send Request / Issue Command
    Router->>Core: Validate & Dispatch Request
    Core->>Store: Query / Mutate State / Call Upstream
    Store-->>Core: Return State / Response Data
    Core-->>Router: Format Domain Output
    Router-->>Client: Return Result
{fence}
"""
    write_text_safe(dest_path, content)


def write_architecture_api_contracts(dest_path: str, info: dict[str, Any], ai_synth: dict[str, Any] | None = None) -> None:
    proj_name = str(info.get("project_name", "Project"))
    primary_lang = str(info.get("languages", ["Application"])[0])

    if ai_synth and ai_synth.get("api_contracts_summary"):
        summary = str(ai_synth["api_contracts_summary"])
    else:
        summary = f"Public interfaces, exported symbols, and CLI/API contracts for {proj_name}."

    raw_cmds = info.get("build_commands", [])
    cmds = cast(list[dict[str, Any]], raw_cmds) if isinstance(raw_cmds, list) else []

    cmd_rows = ""
    for c in cmds:
        cmd_rows += f"| `{c.get('command')}` | `{c.get('name')}` | Project Build / Verification Task |\n"

    if not cmd_rows:
        cmd_rows = f"| `{proj_name.lower()}` | Entrypoint | Main {primary_lang} execution binary/script |\n"

    content = f"""# API & Interface Contracts

## Interface Summary
{summary}

## Project Commands & Scripts
| Command / Target | Purpose | Description |
| --- | --- | --- |
{cmd_rows.strip()}
"""
    write_text_safe(dest_path, content)


def write_architecture_dependencies(dest_path: str, info: dict[str, Any]) -> None:
    raw_langs = info.get("languages", ["Python"])
    langs = cast(list[str], raw_langs) if isinstance(raw_langs, list) else ["Python"]

    raw_frameworks = info.get("frameworks", [])
    frameworks = cast(list[str], raw_frameworks) if isinstance(raw_frameworks, list) else []

    content = f"""# Dependency & Technology Matrix

## Runtime Languages
{chr(10).join([f"- **{l}**" for l in langs])}

## Frameworks & Dependencies
{chr(10).join([f"- **{f}**" for f in frameworks]) if frameworks else "- Standard library"}
"""
    write_text_safe(dest_path, content)


def write_architecture_domain_models(dest_path: str, symbols: list[dict[str, str]]) -> None:
    lines = [
        "# Domain Models & Core Entities",
        "",
        "This document catalogs extracted domain models, structs, classes, and interfaces from the codebase.",
        ""
    ]
    if symbols:
        for s in symbols:
            lines.append(f"- **`{s.get('name')}`** ({s.get('kind')} in `{s.get('file')}`)")
    else:
        lines.append("- Core entities governed by modular application models.")

    write_text_safe(dest_path, "\n".join(lines) + "\n")


def write_lessons_learned(lessons_dir: str, ai_synth: dict[str, Any] | None = None) -> None:
    decisions_path = os.path.join(lessons_dir, "architectural-decisions.md")
    rules_list: list[str] = []
    if ai_synth and isinstance(ai_synth.get("invariants_and_rules"), list):
        rules_list = [f"- **Rule**: {r}" for r in ai_synth["invariants_and_rules"]]
    if not rules_list:
        rules_list = [
            "- **Separation of Concerns**: Maintain modular boundaries between controllers, business logic, and storage.",
            "- **Error Handling**: Use explicit error propagation and avoid suppressing runtime errors."
        ]

    decisions_content = "# Architectural Decisions & Invariants\n\n## Project Invariants & Design Rules\n" + "\n".join(rules_list) + "\n"
    write_text_safe(decisions_path, decisions_content)

    problems_path = os.path.join(lessons_dir, "known-problems.md")
    pitfalls_list: list[str] = []
    if ai_synth and isinstance(ai_synth.get("known_pitfalls"), list):
        pitfalls_list = [f"- **Pitfall**: {p}" for p in ai_synth["known_pitfalls"]]
    if not pitfalls_list:
        pitfalls_list = [
            "- **State Concurrency**: Ensure thread-safe access to shared in-memory data structures.",
            "- **Resource Cleanup**: Properly close file handles, database connections, and network sockets."
        ]

    problems_content = "# Known Problems & Anti-Patterns\n\n## Pitfalls & Design Constraints\n" + "\n".join(pitfalls_list) + "\n"
    write_text_safe(problems_path, problems_content)


__all__ = [
    "generate_project_summary",
    "write_project_summary",
    "write_architecture_overview",
    "write_architecture_components",
    "write_architecture_data_flows",
    "write_architecture_api_contracts",
    "write_architecture_dependencies",
    "write_architecture_domain_models",
    "write_lessons_learned",
]
