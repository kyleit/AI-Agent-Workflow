---
name: python-development
command: python-dev
aliases:
  - python
  - py
category: implementation
tags:
  - python
  - backend
  - testing
  - linting
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Guides python development tasks including package management, testing, formatting, and linting.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: cached
---

# Skill: python-development (Python Implementation Guidelines)

## 1. Purpose
Provides comprehensive, structured guidelines and validation steps for Python implementation, formatting, testing, and debugging.

## 2. Workflow Runtime & Initialization Check
This Skill is invoked dynamically by `blueprint-to-implementation` routing based on the target project tech stack. It does not directly manage workflow checkpoints or session state updates.

## 3. Global Policy References
Adheres strictly to the policies defined in `AI_RULES.md`:
- **Approval Gate Policy** (Section 1) - Seek confirmation before modifying code.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits with approval.
- **Memory First Policy** (Section 3) - Search codebase/memory first.
- **RAG Policy** (Section 4) - Level-based query sequences.
- **Testing Policy** (Section 8) - Run test validation suites.

## 4. Public APIs / Trigger Contract
- **Commands**: `python-dev`
- **Aliases**: `python`, `py`
- **File Patterns**: `*.py`, `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`

## 5. Workflow Integration
When `blueprint-to-implementation` executes, it detects Python files within the scope of changes and routes specific code modifications and validation commands to this skill.

## 6. Language-Specific Guidance
- **Codebase-First & RAG-First**: Search using `grep` or semantic search first. Align with existing patterns.
- **Iterative Execution Loop**: Plan -> Draft minimal changes -> Test & Lint -> Fix -> Verify.
- **Debugging**: Read traceback from bottom to top. Run isolated test cases (`pytest path/to/test.py::test_name`).
- **Testing with Pytest**: Group tests in `test_*.py`. Use fixtures and mocking (`unittest.mock`).
- **Refactoring**: Short, SRP compliant functions. Clear PEP 257 docstrings.
- **Performance**: Use generator expressions for large data. Process large files line-by-line.
- **Database Integrity**: Define ORM structures (SQLAlchemy, Peewee). Use migrations (Alembic) instead of manual table modifications.
- **Git & Architecture**: Keep commits atomic. Follow clean layering (Controllers, Services, Repositories).

## 7. Validation Commands
Before completion, ensure all tests and checkers pass:
- **Formatting**: `black --check .` and `isort --check .`
- **Linting**: `flake8 .` or `pylint <module>`
- **Type Checking**: `mypy .`
- **Unit Testing**: `pytest -v`

## 8. Provider Strategy
Provider agnostic. Emphasizes local environment tooling and project RAG analysis before LLM generation.

## 9. Backward Compatibility
Fully compatible with Python 3.8+ environments. Reuses existing config configurations.

## 10. Usage Examples
- Run formatting and check:
  ```bash
  black . && isort . && pytest -v
  ```

## 11. Extension Points
Custom linting hooks or formatting engines can be appended in `pyproject.toml` configurations.

## 12. Limitations
Requires Python SDK environment configured correctly on the user host machine.
