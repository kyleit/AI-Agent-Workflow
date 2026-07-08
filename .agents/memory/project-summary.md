# Project Summary

## Project Name
ai-skill-framework

## Business Domain & Purpose
A reusable collection of engineering skills for AI coding agents to manage SDLC lifecycle

## Primary Language
Python

## Secondary Languages
PowerShell, Shell, JavaScript, HTML, CSS

## Frameworks & Libraries


## Architecture Style
Multi-Agent Orchestrated SDLC Workflow.

## Main Modules
- **Workflow Runtime** (`skills/workflow-runtime`): Python-based CLI runtime engine that manages execution sessions and SQLite backed metrics. Backed by SQLite database and manages .session.json updates.
- **SDLC Skills Library** (`skills`): Collection of 22 modular software engineering skills (e.g. blueprint-to-implementation, brainstorming, brainstorming-to-plan). Includes 22 independent prompt-driven or script-first modules.


## Databases & Storage Backends
- **SQLite** (`.agents/project_runtime.db`): Persists active session usage, checkpoint status, and global metrics.


## External Services & Integrations
- Google Gemini & Anthropic Claude (LLM providers for workflow skills execution).

## Build Commands
- None

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
2026-07-08

## Memory Version
1.0.0
