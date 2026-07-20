---
name: python-patterns
command: python-patterns
aliases:
  - python-architecture
  - python-design
category: architecture
tags:
  - python
  - architecture
  - patterns
  - framework-selection
version: 1.0.0
license: MIT
created_at: 2026-07-15
updated_at: 2026-07-15
description: Guides python design patterns, architecture decisions, OOP principles, and clean code practices.
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
  usage: cached---

# Skill: python-patterns (Python Architecture Patterns)

## 1. Purpose
Provides comprehensive architectural guidance, framework selection rules, and modern Python design patterns.

## 2. Workflow Runtime & Initialization Check
This Skill is invoked during architectural design phase by `blueprint-to-implementation` or planning skills. It does not directly manage workflow checkpoints or session state updates.

## 3. Global Policy References
Adheres strictly to the policies defined in `AI_RULES.md`:
- **Approval Gate Policy** (Section 1) - Seek confirmation before introducing new structures.
- **Memory First Policy** (Section 3) - Search codebase first to align with existing architecture.
- **Blueprint Mandatory Execution Policy** (Section 13) - Design changes must reflect in blueprints.

## 4. Public APIs / Trigger Contract
- **Commands**: `python-patterns`
- **Aliases**: `python-architecture`, `python-design`
- **File Patterns**: `docs/blueprints/**/*.md`, `docs/blueprints/**/*.json`, Python structure files.

## 5. Workflow Integration
Invoked automatically when planning architectural designs or during discovery to match frameworks and design paradigms.

## 6. Language-Specific Guidance
- **Framework Selection**: 
  - *FastAPI*: High-performance asynchronous REST APIs.
  - *Django*: Full-featured database-backed monolithic web apps (ORM, Admin).
  - *Flask*: Simple microservices, prototypes, single-purpose scripts.
  - *Click/Typer*: For type-hint based CLI tool parsing.
- **Async vs Sync**:
  - *Async*: For I/O-bound tasks. Use `asyncio.to_thread` or `loop.run_in_executor` for sync drivers.
  - *Sync*: For CPU-bound tasks (run in `ProcessPoolExecutor`).
- **Strict Type Hinting**: Enforce annotations. Use `typing` / built-in collections (`list[str]`, `dict[str, int]`). Use `Optional` or `T | None`.
- **Pydantic & Dataclasses**: Use Pydantic at boundaries (request body validation). Use Dataclasses (`frozen=True`) for internal DTOs.
- **Directory Structure**: Separate concerns cleanly (src/core, src/domain, src/application, src/infrastructure).
- **Clean Architecture & DDD**: Pure Domain layer (no external frameworks). Application services. Infrastructure layers. Dependency Inversion with PEP 544 Protocols.

## 7. Validation Commands
- **Type Checking**: `mypy .`

## 8. Provider Strategy
Provider agnostic. Emphasizes clean code architectures that are model-readable.

## 9. Backward Compatibility
Compatible with Python 3.8+.

## 10. Usage Examples
- Structuring a domain Protocol:
  ```python
  from typing import Protocol

  class UserRepository(Protocol):
      def get_by_id(self, user_id: int) -> dict[str, str] | None: ...
  ```

## 11. Extension Points
Architectural design rules can be modified via custom templates.

## 12. Limitations
Focuses on design structure rather than CLI runtime checking.
