# markdown_writer.py
import os
from datetime import datetime

def generate_project_summary(info: dict) -> str:
    langs = info.get("languages", ["Unknown"])
    primary_lang = langs[0] if langs else "Unknown"
    secondary_langs = langs[1:] if len(langs) > 1 else []
    
    modules_str = ""
    for mod in info.get("modules", []):
        modules_str += f"- **{mod['name']}** (`{mod['path']}`): {mod['purpose']} {mod.get('details', '')}\n"
        
    db_str = ""
    for db in info.get("databases", []):
        db_str += f"- **{db['type']}** (`{db['path']}`): {db['purpose']}\n"
        
    build_str = ""
    for cmd in info.get("build_commands", []):
        build_str += f"- `{cmd['command']}` ({cmd['name']})\n"
        
    md = f"""# Project Summary

## Project Name
{info.get("project_name", "ai-skill-framework")}

## Business Domain & Purpose
{info.get("description", "A reusable collection of engineering skills for AI coding agents to manage SDLC lifecycle.")}

## Primary Language
{primary_lang}

## Secondary Languages
{", ".join(secondary_langs) if secondary_langs else "- None"}

## Frameworks & Libraries
{", ".join(info.get("frameworks", ["None"]))}

## Architecture Style
Multi-Agent Orchestrated SDLC Workflow.

## Main Modules
{modules_str if modules_str else "- None"}

## Databases & Storage Backends
{db_str if db_str else "- None"}

## External Services & Integrations
- Google Gemini & Anthropic Claude (LLM providers for workflow skills execution).

## Build Commands
{build_str if build_str else "- None"}

## Test/Verification Commands
- `python3 -m unittest skills/workflow-runtime/tests/test_runtime.py` (to run Runtime CLI Engine unit tests).

## Deployment Method
- Package Visualizer into VSIX (`make package`).
- Distribute scripts to `.agents/` customization root.

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

def write_project_summary(dest_path: str, info: dict):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    content = generate_project_summary(info)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)

def write_architecture_overview(dest_path: str, info: dict):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    content = f"""# Architecture Overview

## Structural Overview
Kiến trúc dự án dựa trên mô hình điều phối đa tác nhân (Multi-Agent). Các tệp tin kỹ năng được thiết lập dưới dạng các chỉ thị độc lập trong thư mục `skills/` và được theo dõi trạng thái qua tệp phiên làm việc cục bộ.

## Technology Stack
- **Ngôn ngữ chính**: TypeScript & Python.
- **Dịch vụ bổ sung**: Qdrant Vector DB để phục vụ truy xuất ngữ cảnh RAG.
- **Hệ thống dữ liệu**: SQLite cục bộ.
"""
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)
