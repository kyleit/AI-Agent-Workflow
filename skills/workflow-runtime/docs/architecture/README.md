# Architecture Overview — workflow_runtime

## Package Structure

```
workflow_runtime/
├── domain/          ← Domain Layer (innermost)
│   ├── entities/    ← Domain Entities and Aggregates
│   ├── services/    ← Domain Services
│   ├── ports/       ← Repository Ports / Abstractions (interfaces)
│   ├── interfaces/  ← Additional interfaces
│   ├── models/      ← Domain Models / Value Objects
│   ├── agent/       ← Agent Routing domain model
│   ├── knowledge/   ← Knowledge domain model
│   ├── security/    ← Security domain model (Permission Boundary)
│   ├── visual/      ← Visual domain model (VIR)
│   ├── workflow/    ← Workflow domain model
│   └── release/     ← Release domain model
│
├── application/     ← Application Layer
│   ├── ports/       ← Application Ports (outbound interfaces)
│   ├── dtos/        ← Data Transfer Objects
│   ├── use_cases/   ← Application Use Cases
│   ├── agent/       ← Agent application services
│   ├── analytics/   ← Usage analytics
│   ├── workflow/    ← Workflow orchestration
│   ├── verification/← Approval/verification gating
│   └── ...          ← Other application services
│
├── infrastructure/  ← Infrastructure Layer (adapters)
│   ├── session/     ← Session storage adapters
│   ├── persistence/ ← DB, lease, checkpoint adapters
│   ├── telegram/    ← Telegram API adapter
│   ├── browser/     ← CDP browser adapter
│   ├── agy/         ← AGY CLI adapter
│   ├── knowledge/   ← Memory/RAG storage adapters
│   └── ...          ← Other infrastructure adapters
│
├── presentation/    ← Presentation Layer (outermost)
│   ├── cli/         ← CLI command handlers
│   ├── api/         ← REST API routers (FastAPI snapshots)
│   └── visual/      ← Visual output formatting
│
└── shared/          ← Cross-cutting utilities
    ├── errors.py    ← Domain exception classes (canonical)
    ├── utils.py     ← Shared utilities
    ├── logging.py   ← Logging configuration
    └── ...
```

---

## Dependency Direction

```
  Presentation (CLI, API)
        ↓
  Application (Use Cases, Services, Ports)
        ↓
  Domain (Entities, Value Objects, Ports)

  Infrastructure (Adapters) → Application Ports ← Domain Ports

  Shared (Errors, Utils) ← All Layers (read-only cross-cutting)
```

### Allowed Dependencies

| FROM | TO | Allowed |
|------|----|----|
| Presentation | Application | ✅ |
| Presentation | Domain | ✅ (DTOs, Types) |
| Presentation | Infrastructure | ❌ FORBIDDEN |
| Application | Domain | ✅ |
| Application | Infrastructure | ❌ FORBIDDEN (DIP violation) |
| Application | Presentation | ❌ FORBIDDEN |
| Infrastructure | Application (Ports) | ✅ |
| Infrastructure | Domain | ✅ |
| Domain | Application | ❌ FORBIDDEN |
| Domain | Infrastructure | ❌ FORBIDDEN |
| Domain | Presentation | ❌ FORBIDDEN |
| Any Layer | Shared | ✅ |
| Shared | Any Layer | ❌ FORBIDDEN |

---

## Composition Root

**Location**: `workflow_runtime/presentation/cli/bootstrap.py`  
Called from: `workflow_runtime/__main__.py` via `bootstrap_di()`

The Composition Root is the ONLY place where:
- Infrastructure adapters are instantiated
- Application use cases receive their concrete dependencies
- DI wiring occurs

**No other module should instantiate concrete Infrastructure classes.**

---

## Import Linter Contracts

All contracts are configured in `pyproject.toml` under `[tool.importlinter]`.

| Contract | Type | Status |
|----------|------|--------|
| Domain Isolation | forbidden | ✅ KEPT |
| Domain Framework Independence | forbidden | ✅ KEPT |
| Application Does Not Import Infrastructure | forbidden | ❌ BROKEN (28 violations) |
| Application Framework Independence | forbidden | ✅ KEPT |
| Presentation Cannot Bypass Application | forbidden | ❌ BROKEN (9 violations) |
| Shared Layer Independence | forbidden | ✅ KEPT |

### Running Architecture Validation

```bash
# Full quality gate
make quality

# Individual gates
make check-file-size    # File size: 0 violations
make typecheck          # Pyright: strict mode
make architecture       # Import Linter: contracts
```

---

## Known Architecture Exceptions

### Exception 1: Presentation → Infrastructure (CLI Layer)

**Files affected**: `presentation/cli/workflow_runtime_shared.py`, various `_impl/` handlers  
**Justification**: The CLI handlers are "thin clients" that were initially written as monolithic scripts. The infrastructure imports are for runtime concerns (session I/O, heartbeats, lease management) that have not yet been fully abstracted into Application Ports.  
**Severity**: HIGH  
**Resolution Plan**: Introduce Application-level Session Management Port and move infrastructure wiring to bootstrap.py.  
**Tracking**: ARCH-VIOLATION-001

### Exception 2: Application → Infrastructure (DIP Violations)

**Files affected**: 28 application service files  
**Justification**: Many Application services directly import concrete Infrastructure adapters due to the monolithic origins of the codebase. This violates the Dependency Inversion Principle.  
**Severity**: HIGH  
**Resolution Plan**: For each affected service, introduce an Application Port (Protocol/ABC) and move instantiation to the Composition Root.  
**Tracking**: ARCH-VIOLATION-002

---

## Dependency Inversion Pattern (Correct)

```python
# domain/ports/repository.py
from typing import Protocol

class UserRepository(Protocol):
    def find_by_id(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

# application/use_cases/create_user.py
class CreateUser:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

# infrastructure/persistence/user_repository_impl.py
class SqliteUserRepository:
    def find_by_id(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

# presentation/cli/bootstrap.py  ← Composition Root
def bootstrap_di() -> None:
    repo = SqliteUserRepository(db_path="...")
    use_case = CreateUser(repository=repo)
```

---

## Pyright Strict Mode

Configuration: `pyrightconfig.json`
```json
{
  "typeCheckingMode": "strict"
}
```

**Current Status**: 12,186 errors in strict mode.  
**Previous Standard Mode**: ~520 errors.

### Error Categories in Strict Mode

| Category | Count | Priority |
|----------|-------|----------|
| reportUnknownMemberType | 3,675 | MEDIUM |
| reportUnknownVariableType | 2,941 | MEDIUM |
| reportUnusedImport | 1,523 | LOW (safe to auto-fix) |
| reportUnknownArgumentType | 1,468 | MEDIUM |
| reportUnknownParameterType | 845 | HIGH |
| reportMissingTypeArgument | 495 | MEDIUM |
| reportMissingParameterType | 312 | HIGH |

---

## File Size Gate

**Limit**: 500 physical lines per Python file  
**Validator**: `scripts/check_python_file_lines.py`  
**Current Status**: ✅ PASS (0 violations, 495 files scanned)

### Running File Size Validation

```bash
python scripts/check_python_file_lines.py
```

---

## Quality Gates Summary

| Gate | Metric | Current | Target | Status |
|------|--------|---------|--------|--------|
| File Size | Files >500 lines | 0 | 0 | ✅ PASS |
| Import Linter | Broken contracts | 2/6 | 0/6 | ❌ FAIL |
| Pyright | Errors (strict) | 12,186 | 0 | ❌ FAIL |
| Domain Isolation | Critical violations | 0 | 0 | ✅ PASS |
| Application→Infra | DIP violations | 28 | 0 | ❌ FAIL |
| Presentation→Infra | Bypass violations | 9 | 0 | ❌ FAIL |
