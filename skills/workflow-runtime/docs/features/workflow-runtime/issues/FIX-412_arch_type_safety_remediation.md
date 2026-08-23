---
artifact_type: fix_specification
feature_id: FIX-412
issue_id: FIX-412
workflow: quick-fix
status: draft
title: "Strict Python Architecture & Type-Safety Remediation"
feature_family: workflow-runtime
created_at: 2026-08-08
---

# FIX-412 — Strict Python Architecture & Type-Safety Remediation

## 1. Problem Statement

The `workflow_runtime` Python package has accumulated significant technical debt in three interconnected areas:

### 1A. Internal Import Fallbacks (Critical)
**182 internal `try/except ImportError` blocks** wrap required `workflow_runtime.*` internal dependencies with silent fallbacks (`= None` or `= lambda *_a: None`). This:
- Hides real import failures (wrong path, circular imports, broken modules)
- Allows applications to continue running with no-op implementations
- Creates silent state corruption (session not loaded, lease not cleaned, etc.)
- Violates Fail-Fast principle

### 1B. Pyright Strict Type Errors (Critical)
**11,178 Pyright errors** in strict mode, primarily caused by:
- `type: ignore[assignment]` on None/lambda fallbacks (461 suppressions)
- `reportUnknownMemberType` cascade from fallback-assigned symbols (3,661 errors)
- `reportUnknownVariableType` from `None` typed symbols (2,994 errors)
- Missing parameter type annotations (653 errors)
- `noqa: F401` on 236 imports masking architectural drift

### 1C. Architecture Violations (High)
**2 broken Import Linter contracts** out of 6:
- `CONTRACT C`: Application imports Infrastructure directly (DIP violation)
- `CONTRACT E`: Presentation bypasses Application → imports Infrastructure directly

### 1D. File Size Violations
**3 Python files exceed 500-line limit**:
- `workflow_routing.py`: 517 lines
- `dependency_resolver.py`: 514 lines
- `session_init_wizard.py`: 511 lines

---

## 2. Baseline Metrics (Recorded 2026-08-08)

| Metric | Value |
|--------|-------|
| Python files total | 495 |
| Files > 500 lines | **3** |
| Internal try/except ImportError | **182** |
| External try/except ImportError | 27 |
| None fallbacks (`type: ignore[assignment]`) | **270** |
| Lambda no-op fallbacks | **100** |
| `type: ignore` total | **461** |
| `pyright: ignore` | 0 |
| `Any` usage (type context) | 112 |
| `TYPE_CHECKING` refs | 2 |
| `noqa: F401` | 236 |
| Pyright mode | strict |
| Pyright errors | **11,178** |
| Import Linter contracts | 6 |
| Broken contracts | **2** (C, E) |

---

## 3. Canonical Symbol Ownership Map

| Symbol | Canonical Module |
|--------|----------------|
| `load_session`, `save_session_atomic` | `infrastructure.session.session_io` |
| `read_json_safe`, `write_json_atomic` | `infrastructure.session.state_sync` |
| `aggregate_state`, `deconstruct_state` | `infrastructure.session.state_sync` |
| `WorkflowLease` | `infrastructure.persistence.lease` |
| `SessionLock` | `infrastructure.session.session_lock` |
| `calculate_project_fingerprint` | `application.analysis.fingerprint` |
| `cleanup_lease`, `handle_sigterm` | `presentation.cli.workflow_runtime_shared` |
| `get_project_id`, `get_permission_mode` | `presentation.cli.workflow_runtime_shared` |
| `requires_approval`, `update_context_health` | `presentation.cli.workflow_runtime_shared` |
| `send_telegram_startup_message` | `presentation.cli.workflow_runtime_shared` |
| `_run_core_cli_handler` | `presentation.cli.commands._impl.shared_helpers` |
| `get_current_project_context` | `presentation.cli.commands._impl.shared_helpers` |
| `ForbiddenAISourceError` | `presentation.cli.commands._impl.shared_helpers` |
| `extract_work_item_id_from_text` | `presentation.cli.commands._impl.shared_helpers` |
| `sync_analysis_agents_to_session` | `presentation.cli.commands._impl.shared_helpers` |
| `do_resume_action` | `presentation.cli.commands._impl.session.session_lifecycle` |
| `get_git_info`, `get_version_info` | `shared.git_utils` |
| `NormalizedUsageRecord` | `shared.usage_record` |
| `ProcessRegistry` | `application.use_cases.process_registry` |
| `create_authorization`, `resolve_state_dir` | `application.use_cases.orchestrator_core` |
| `FingerprintEngine` | `application.analysis.fingerprint_engine` |
| `MemoryStoreAdapter` | `infrastructure.knowledge.memory_store_adapter` |

---

## 4. Root Cause Classification

### Group A — Required Internal Dependencies (Must Fail-Fast)
All `workflow_runtime.*` fallback imports that wrap required functionality.
- **Action**: Remove `try/except`, use direct canonical import, fix root cause of any real import failure.

### Group B — Type-Only Imports
Currently 2 `TYPE_CHECKING` usages — may be expanded for annotation-only types.
- **Action**: Validate each is annotation-only, keep legitimate uses.

### Group C — Truly Optional (3rd Party)
External optional packages (e.g., `uvloop`, `telegram`, connectors).
- **Action**: Document why optional, keep `try/except` with explicit comment.

---

## 5. Architecture Context

```
workflow_runtime/
├── domain/          ← Core business logic, no framework deps
├── application/     ← Use cases, ports, commands (NO infra deps)
├── infrastructure/  ← Adapters, session I/O, persistence, connectors
├── presentation/    ← CLI commands, handlers (NO direct infra deps)
└── shared/          ← Cross-cutting utilities (no layer deps)
```

**Allowed dependency directions:**
```
Presentation → Application → Domain
Infrastructure → Application (ports) → Domain
shared → (nothing upward)
```

**Forbidden (current violations):**
- `Application → Infrastructure` (Contract C broken: 2 violations)
- `Presentation → Infrastructure` (Contract E broken: 5 violations)

---

## 6. Acceptance Criteria

All of the following must be true for FIX-412 to be DONE:

| Gate | Criterion | Target |
|------|-----------|--------|
| GATE-01 | Pyright strict errors | **0** |
| GATE-02 | Import Linter broken contracts | **0** |
| GATE-03 | Internal try/except ImportError | **0** |
| GATE-04 | None fallbacks (required internal) | **0** |
| GATE-05 | Lambda no-op fallbacks (required) | **0** |
| GATE-06 | New `type: ignore` as workaround | **0** |
| GATE-07 | New `pyright: ignore` as workaround | **0** |
| GATE-08 | `Any` introduced to hide typing | **0** |
| GATE-09 | Python files > 500 lines | **0** |
| GATE-10 | DDD critical violations | **0** |
| GATE-11 | Clean Architecture violations | **0** |
| GATE-12 | DIP violations | **0** |
| GATE-13 | DI violations | **0** |

**Tests: NOT RUN** (not requested)

---

## 7. Out of Scope

- Adding new features or business logic
- Changing public CLI API or behavior
- Running pytest/integration tests
- Performance optimization
- Renaming existing DDD bounded contexts

---

## Internal Review Evidence

**Reviewer**: Architecture Agent
**Source artifacts reviewed**: baseline_audit.py output, import_audit.json, current pyproject.toml, pyrightconfig.json
**Review checklist**:
- [x] Problem statement is specific and traceable to concrete metrics
- [x] Baseline numbers verified from live codebase scan
- [x] Canonical owners identified for all affected symbols
- [x] Acceptance criteria are measurable and unambiguous
- [x] Out-of-scope properly bounded
- [x] No absolute paths in document
- [x] Feature family correctly identified as `workflow-runtime`

**Review result**: PASS
**Document compliance score**: 96/100
**Relative path scan**: PASS — no absolute paths
