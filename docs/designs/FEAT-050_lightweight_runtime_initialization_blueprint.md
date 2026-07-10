<!-- File path: docs/designs/FEAT-050_lightweight_runtime_initialization_blueprint.md -->

---
feature_id: FEAT-050
feature_name: Lightweight Runtime Initialization & Runtime Dependency Resolver
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
patch_version: v1.2
previous_artifact: ../plans/FEAT-050_lightweight_runtime_initialization_plan.md
next_artifact: Implementation (Source Code)
related_adr: ../adr/ADR-005_runtime_dependency_resolver.md
---

# Technical Design Blueprint & Implementation Contract – Lightweight Runtime Initialization & Runtime Dependency Resolver

## 0. Baseline Context & References
- **Memory Baseline**: Codebase reviewed at high confidence. All target modules (`workflow_runtime.py`, `session.py`, `state_sync.py`, `context.py`, `validator.py`, `utils.py`) examined directly.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (lines 1–338) — entrypoint, `update_context_health`, `do_start`, `do_complete`
  - `skills/workflow-runtime/scripts/session.py` (lines 1–80) — `load_session`, `save_session_atomic`, `SESSION_FILE` path
  - `skills/workflow-runtime/scripts/context.py` (lines 1–410) — `parse_transcript`, `sync_request_history`, `refresh_context_usage_for_active_conversation`
  - `skills/workflow-runtime/scripts/validator.py` (lines 1–89) — `get_git_info`, `get_version_info`
  - `skills/workflow-runtime/scripts/utils.py` (lines 1–60) — `get_memory_info`, `get_rag_info`
- **RAG Queries**: None performed — context fully established from direct source inspection.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/initialize-workflow/SKILL.md` | MODIFY | Remove heavy init steps; declare `runtime_requirements` | None | Low — documentation only |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Add `deps` subcommand group; hook `resolve_requirements()` in `do_start`; strip heavy calls from `update_context_health` | `dependency_resolver.py` | High — central entrypoint |
| `skills/workflow-runtime/scripts/dependency_resolver.py` | NEW | Core resolver + task graph + state machine + phase gate + next-task logic | `session.py`, `validator.py`, `utils.py` | Medium — new module |
| `skills/workflow-runtime/scripts/task_orchestrator.py` | NEW | Task ledger reader/writer, task state transitions, graph validator | `dependency_resolver.py`, `state_sync.py` | Medium — new module |
| `skills/workflow-runtime/scripts/context.py` | MODIFY | Add `load_memory_lazy()`, `load_rag_lazy()`, `load_memory_cached()`, `load_rag_cached()`, `load_version_cached()`, `load_provider_cached()`, `load_usage_cached()`, `block_workspace_scan()` wrappers | None | Medium — lazy load paths |
| `skills/workflow-runtime/scripts/validator.py` | MODIFY | Replace live git/env checks with cached readers; add `read_environment_snapshot()`, `detect_work_item_cached()`, `detect_project_version_cached()` | None | Low — isolated functions |
| `skills/workflow-runtime/scripts/session.py` | MODIFY | Add `load_guardrails_summary()`, `load_approval_state()`, `load_dashboard_state()` | `state_sync.py` | Low — additive |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Add `write_initialization_summary()`, `validate_no_heavy_init_operations()` helpers | None | Low — additive |
| All core `SKILL.md` files (×12) | MODIFY | Add `runtime_requirements` frontmatter block (updated schema with version/provider/usage) | None | Low — documentation only |
| `extensions/visualizer/src/extension.ts` | AUDIT | Verify session/state reader compatibility with split-state | None | Medium — reads `.session.json` directly |
| `extensions/visualizer/resources/webview.html` | AUDIT | Verify dashboard prefers `dashboard.json` over `.session.json` | None | Low |
| `skills/workflow-runtime/tests/test_dependency_resolver.py` | NEW | Unit tests for resolver logic | `dependency_resolver.py` | None |
| `skills/workflow-runtime/tests/test_runtime_requirements_schema.py` | NEW | Unit tests for manifest schema parsing | `dependency_resolver.py` | None |
| `skills/workflow-runtime/tests/test_dependency_resolver_cli.py` | NEW | CLI tests for `deps` subcommand group (including `deps fix`) | `workflow_runtime.py` | None |
| `skills/workflow-runtime/tests/test_lightweight_initialize.py` | NEW | Performance & compatibility & no-heavy-init tests | `workflow_runtime.py` | None |
| `skills/workflow-runtime/tests/test_phase_completion_gate.py` | NEW | Phase coverage gate tests | `dependency_resolver.py` | None |
| `skills/workflow-runtime/tests/test_task_dependency_graph.py` | NEW | Task graph creation, cycle detection, missing ref detection | `task_orchestrator.py` | None |
| `skills/workflow-runtime/tests/test_task_state_machine.py` | NEW | State machine transition validation | `task_orchestrator.py` | None |
| `skills/workflow-runtime/tests/test_next_ready_task.py` | NEW | Next-task recommendation logic | `task_orchestrator.py` | None |
| `skills/workflow-runtime/tests/test_deps_fix.py` | NEW | `deps fix` auto-fix command tests | `workflow_runtime.py` | None |
| `docs/guides/runtime-dependency-resolver.md` | NEW | Usage guide for dependency resolver | None | None |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/
├── scripts/
│   ├── workflow_runtime.py        [MODIFY] — add deps subcommands, hook resolver
│   ├── dependency_resolver.py     [NEW]    — core resolver module
│   ├── context.py                 [MODIFY] — lazy load wrappers
│   ├── validator.py               [MODIFY] — cached env/git/version readers
│   ├── session.py                 [MODIFY] — guardrail/approval state loaders
│   ├── state_sync.py              [MODIFY] — init summary helpers
│   └── ... (existing scripts unchanged)
├── tests/
│   ├── test_dependency_resolver.py          [NEW]
│   ├── test_runtime_requirements_schema.py  [NEW]
│   ├── test_dependency_resolver_cli.py      [NEW]
│   ├── test_lightweight_initialize.py       [NEW]
│   ├── test_phase_completion_gate.py        [NEW]
│   ├── test_task_dependency_graph.py        [NEW]
│   ├── test_task_state_machine.py           [NEW]
│   ├── test_next_ready_task.py              [NEW]
│   └── test_deps_fix.py                     [NEW]
skills/initialize-workflow/
└── SKILL.md                       [MODIFY] — lightweight instructions + runtime_requirements
extensions/visualizer/
├── src/extension.ts               [AUDIT]  — verify reads dashboard.json, not raw .session.json
└── resources/webview.html         [AUDIT]  — verify release_allowed flag from dashboard
.agents/
└── state/
    ├── runtime/
    │   └── dependencies.json      [NEW]    — resolution state output
    └── workflow/
        ├── task_graph.json        [NEW]    — task dependency graph with states
        └── tasks.json             [NEW]    — task ledger (source of truth for progress)
docs/
├── guides/
│   └── runtime-dependency-resolver.md  [NEW]
└── adr/
    └── ADR-005_runtime_dependency_resolver.md  [ALREADY CREATED]
```

---

## 3. Complete Class & Module Design

### Module: `dependency_resolver.py`

- **Responsibilities**: Parse `runtime_requirements` from SKILL.md YAML frontmatter; validate keys and modes; resolve dependencies in correct order; record state to `dependencies.json`.
- **Constants**:
  - `SUPPORTED_KEYS = {"rules", "state", "approvals", "git", "memory", "rag", "workspace_scan", "environment", "provider_usage", "transcript_sync"}`
  - `SUPPORTED_MODES = {"required", "cached", "lazy", "optional", "none"}`
  - `SAFETY_KEYS = {"rules", "state", "approvals"}` — always forced to `required`, cannot be overridden
  - `DEPENDENCIES_FILE = os.path.join(".agents", "state", "runtime", "dependencies.json")`

- **Public Functions**:

  - `parse_requirements(skill_name: str) -> dict`
    - Read the SKILL.md at `skills/<skill_name>/SKILL.md`
    - Extract YAML frontmatter between `---` delimiters
    - Return `runtime_requirements` dict, or `{}` if not found (legacy fallback)

  - `validate_requirements(skill_name: str, requirements: dict) -> ValidationResult`
    - Check all keys are in `SUPPORTED_KEYS`
    - Check all values are in `SUPPORTED_MODES`
    - Check `SAFETY_KEYS` are never set to `lazy`, `optional`, or `none`
    - Return `ValidationResult(ok: bool, errors: list[str], warnings: list[str])`

  - `resolve_requirements(skill_name: str, requirements: dict) -> ResolvedRuntimeContext`
    - For each key in requirements, call `load_required_dependency(key, mode)`
    - Collect results into `ResolvedRuntimeContext`
    - Write output to `DEPENDENCIES_FILE`
    - Return context

  - `load_required_dependency(name: str, mode: str) -> DependencyResult`
    - Dispatch to loader by key:
      - `rules` → `load_guardrails_summary()` (hashed summary) + full load only when skill requires full policy text
      - `state` → `load_state()` (read `.agents/state/context.json`)
      - `approvals` → `load_approvals()` (read `.agents/state/approvals.json`)
      - `git` → `load_git_cached()` — **ALLOWED**: `git branch --show-current`, `git status --short`, `git rev-parse --is-inside-work-tree` only
      - `memory` → dispatched by mode: `cached` → `load_memory_cached()`, `lazy` → `load_memory_lazy()`, `required` → `load_memory_required()`
      - `rag` → dispatched by mode: `cached` → `load_rag_cached()`, `lazy` → `load_rag_lazy()`, `required` → `load_rag_required()`
      - `environment` → `read_environment_snapshot()` (read `.agents/state/environment.json`; NEVER run CLI version checks)
      - `workspace_scan` → `check_workspace_scan_allowed(skill_name, mode)`
      - `provider_usage` → optional: read from `.agents/state/context/usage.json` or `dashboard.json` only
      - `transcript_sync` → **HARD BLOCKED** in `initialize-workflow`; only called when skill declares `transcript_sync: required`

  > **HARD RULE**: `initialize-workflow` MUST NOT call `sync_request_history()`, `parse_transcript()`, `refresh_context_usage_for_active_conversation()`, or any transcript directory scan. Usage/token data must come only from `.agents/state/context/usage.json` or `.agents/state/dashboard.json`. If stale, warn only.

  - `get_doctor_report(strict_mode: bool = False) -> DoctorReport`
    - Scan all `skills/*/SKILL.md` files
    - For each: call `parse_requirements()` and `validate_requirements()`
    - Report: missing declarations, invalid keys, safety key violations, unnecessary workspace_scan
    - If `strict_mode=True`: missing `runtime_requirements` → **error** (blocks execution)
    - If `strict_mode=False`: missing `runtime_requirements` → **warning** (applies `safe_minimal` fallback, logs to doctor report)
    - `safe_minimal` fallback (applied to legacy skills without declarations):
      - loads `rules` (required)
      - loads `state` (required)
      - loads `approvals` if file exists (optional)
      - reads git branch/status only (cached)
      - does NOT load memory
      - does NOT load RAG
      - does NOT scan workspace
      - does NOT check environment tools
      - does NOT parse transcripts or sync request history

  - `validate_phase_completion(phase_id: str, task_graph: TaskGraph, task_ledger: TaskLedger) -> PhaseCoverageResult`
    - A phase is complete ONLY when ALL of the following hold:
      1. Every task in `phase.tasks` exists in `tasks.json` (ledger consistency check)
      2. Every task has state `completed`
      3. Every task's `verification_status` is `pass` or `not_configured`
      4. No required task is `skipped` without an explicit `approved_skip_reason`
      5. No task in phase is `queued`, `waiting`, `ready`, `running`, `blocked`, `failed`, or `aborted`
      6. All phase exit criteria pass
      7. Active worker count for phase is zero
      8. Active lock count for phase is zero
    - Returns `PhaseCoverageResult(ok: bool, phase_id: str, incomplete_tasks: list[str], failed_criteria: list[str])`
    - **Hard Rule**: `Phase Complete != First Blocking Task Complete`
    - **Failure output example**:
      ```text
      Phase completion blocked.

      Phase: phase-1
      Required tasks: 3
      Completed: 1
      Incomplete:
      - Task 1.2: ready
      - Task 1.3: waiting on Task 1.2

      Next action:
      Continue implementation with Task 1.2.
      ```

  - `get_next_ready_task(task_graph: TaskGraph, task_ledger: TaskLedger) -> str | None`
    - Returns the next actionable task name, or `None` if blocked.
    - Rules (evaluated in priority order):
      1. If any task is `running` → return `None` with message `"Wait or recover running task first."`
      2. If any task is `failed` → return `None` with message `"Recover failed task before continuing."`
      3. Scan `ready_queue` in task graph → return first task whose all dependencies are `completed`
      4. If current phase has incomplete tasks → stay in current phase, do NOT advance
      5. Only when ALL tasks in current phase are complete → recommend next phase entry task
      6. Only when ALL phases are complete → recommend `/debug`
      7. **NEVER** recommend `/release` before all phases + debug PASS + verify PASS


- **Data Classes**:
  ```python
  @dataclass
  class ValidationResult:
      ok: bool
      errors: list[str]
      warnings: list[str]

  @dataclass
  class DependencyResult:
      name: str
      mode: str
      status: str  # "loaded" | "cached" | "deferred" | "skipped" | "missing" | "stale"
      source: str
      action: str  # "warn_only" | "block" | "defer"
      data: dict | None = None

  @dataclass
  class ResolvedRuntimeContext:
      skill: str
      resolved_at: str
      requirements: dict
      resolved: dict[str, DependencyResult]
      missing_required: list[str]
      warnings: list[str]

  @dataclass
  class PhaseCoverageResult:
      ok: bool
      phase_id: str
      incomplete_tasks: list[str]
      failed_criteria: list[str]
  ```

### Module: `task_orchestrator.py` — **[NEW]**

- **Responsibilities**: Build and validate task dependency graph; enforce task state machine transitions; manage task ledger (`tasks.json`); compute next ready task.
- **State File**: `.agents/state/workflow/task_graph.json`, `.agents/state/workflow/tasks.json`
- **Constants**:
  - `VALID_STATES = {"queued", "waiting", "ready", "running", "blocked", "completed", "failed", "skipped", "aborted"}`
  - `ALLOWED_TRANSITIONS = {"queued": {"waiting", "ready"}, "waiting": {"ready"}, "ready": {"running", "skipped"}, "running": {"completed", "failed", "blocked", "aborted"}, "failed": {"queued"}, "blocked": {"ready"}, "completed": set(), "skipped": set(), "aborted": set()}`
  - `FORBIDDEN_SHORTCUTS = [("queued", "completed"), ("waiting", "completed"), ("running", "queued"), ("completed", "running")]`

- **Public Functions**:

  - `build_task_graph(plan_json: dict) -> TaskGraph`
    - Derives graph from `phases[]` and `tasks[]` in plan JSON
    - Validates for cycles using DFS; raises `CyclicDependencyError` if cycle found
    - Validates all dependency references exist; raises `UnknownDependencyError` if not
    - Writes result to `.agents/state/workflow/task_graph.json`

  - `transition_task_state(task_id: str, new_state: str, ledger: TaskLedger, reason: str = "") -> bool`
    - Checks transition is in `ALLOWED_TRANSITIONS`
    - Raises `ForbiddenStateTransitionError` for any transition in `FORBIDDEN_SHORTCUTS`
    - `completed` is only reachable when: implementation done + expected outputs exist + verification passes + no active worker + no active lock
    - Writes updated task to `tasks.json`

  - `load_task_ledger() -> TaskLedger`
    - Reads `.agents/state/workflow/tasks.json`
    - Raises `LedgerConsistencyError` if a blueprint task is missing from ledger

  - `write_task_ledger(ledger: TaskLedger) -> None`
    - Atomically writes to `.agents/state/workflow/tasks.json`

  - `get_next_ready_task(task_graph: TaskGraph, task_ledger: TaskLedger) -> tuple[str | None, str]`
    - Returns `(task_id, reason)` or `(None, reason)`
    - See recommendation logic in `dependency_resolver.py` section above

- **Data Classes**:
  ```python
  @dataclass
  class TaskNode:
      task_id: str
      phase_id: str
      dependencies: list[str]
      dependents: list[str]
      state: str
      required: bool
      verification_status: str  # "pending" | "pass" | "fail" | "not_configured"
      attempt: int
      worker_id: str | None
      lock_ids: list[str]

  @dataclass
  class TaskGraph:
      feature_id: str
      graph_version: str
      phases: dict[str, dict]
      tasks: dict[str, TaskNode]
      ready_queue: list[str]
      blocked_tasks: list[str]
      failed_tasks: list[str]
      completed_tasks: list[str]

  @dataclass
  class TaskLedger:
      feature_id: str
      current_phase: str
      current_task: str
      tasks_total: int
      tasks_completed: int
      tasks: dict[str, dict]
  ```

---

## 4. Detailed Interface Contracts

### `parse_requirements(skill_name: str) -> dict`
- **Parameters**: `skill_name` — the skill directory name under `skills/`
- **Returns**: `dict` of `runtime_requirements` keys and modes, or `{}` for legacy skills
- **Exceptions**: Silently returns `{}` on file not found or YAML parse error
- **Notes**: Reads only YAML frontmatter between first `---` pair; does not load body

### `validate_requirements(skill_name: str, requirements: dict) -> ValidationResult`
- **Parameters**: `skill_name` (for error messages), `requirements` (parsed dict)
- **Returns**: `ValidationResult` with `ok=True` if no errors
- **Exceptions**: None raised — errors returned in result
- **Validation Rules**:
  - Unknown key → error
  - Unknown mode → error
  - Safety key (`rules`, `state`, `approvals`) set to `lazy`/`optional`/`none` → error

### `resolve_requirements(skill_name: str, requirements: dict) -> ResolvedRuntimeContext`
- **Parameters**: `skill_name`, validated `requirements`
- **Returns**: `ResolvedRuntimeContext` with all resolution outcomes
- **Exceptions**: `RuntimeError` if a `required` dependency fails to load and there is no fallback
- **Side Effects**: Writes `.agents/state/runtime/dependencies.json`

### `read_environment_snapshot() -> DependencyResult` (in `validator.py`)
- **Returns**: `DependencyResult` with status `"loaded"` or `"stale"` or `"missing"`
- **Stale Check**: If `environment.json` `updated_at` is older than 24 hours → status = `"stale"`, action = `"warn_only"`
- **Missing**: If `environment.json` does not exist → status = `"missing"`, action = `"warn_only"`, message = `"Run /environment-health to generate a fresh snapshot."`
- **Never**: Does NOT run `python --version`, `docker version`, `go version`, etc.

### `detect_work_item_cached() -> dict` (in `validator.py`)
- **Returns**: `{"id": "FEAT-050", "type": "FEAT", "title": "..."}` from `.agents/state/context.json`
- **Never**: Does NOT scan `docs/` filesystem directories

### `detect_project_version_cached() -> str` (in `validator.py`)
- **Returns**: version string from `.agents/state/context.json` → `version.version` field
- **Never**: Does NOT read `package.json`, `pyproject.toml`, `go.mod`, etc.

### `load_guardrails_summary() -> dict` (in `session.py`) — **[PATCHED: script-first RULES tracking]**
- **Returns**:
  ```json
  {
    "rules_loaded": true,
    "ai_rules_hash": "sha256:...",
    "agents_hash": "sha256:...",
    "active_skill_hash": "sha256:...",
    "policy_flags": {
      "approval_gate": true,
      "git_gate": true,
      "blueprint_gate": true,
      "release_gate": true,
      "testing_gate": true,
      "workspace_permission_gate": true
    }
  }
  ```
- **Notes**: Does NOT weaken rules. Full `AI_RULES.md` text is still loaded when skill requires complete policy reasoning. This summary is for runtime state and dashboard display only.

### `load_memory_cached() -> DependencyResult` (in `context.py`) — **[PATCHED: precise semantics]**
- **Behaviour**: Reads ONLY lightweight memory metadata — `memory-state.json` and `memory.config.json`
- **Never**: Does NOT read `project-summary.md` or any module memory documents
- **Status returned**: `cached`

### `load_memory_lazy(query: str | None = None) -> DependencyResult` (in `context.py`) — **[PATCHED]**
- **Parameters**: `query` — optional targeted query string
- **With no query**: Returns a `deferred` handle — nothing is loaded
- **With query**: Loads only targeted memory chunks/documents matching the query
- **Never**: Does NOT load full `memory-state.json` by default

### `load_memory_required(targets: list[str] | None = None) -> DependencyResult` (in `context.py`) — **[NEW]**
- **Allowed only for**: `project-memory-bootstrap`, `project-memory-update`
- **Behaviour**: May load `project-summary.md` and specific required memory documents
- **Never**: Does NOT load entire memory index unless `targets=None` and skill is explicitly allowed

### `load_rag_cached() -> DependencyResult` (in `context.py`) — **[PATCHED: precise semantics]**
- **Behaviour**: Reads RAG metadata/status only — does NOT connect or query vector DB
- **Status returned**: `cached`

### `load_rag_lazy(query: str | None = None) -> DependencyResult` (in `context.py`) — **[PATCHED]**
- **Parameters**: `query` — optional semantic query string
- **With no query**: Returns a `deferred` handle — nothing is loaded
- **With query**: Issues targeted RAG query against the vector index
- **Never**: Does NOT initialize the full vector index during init

### `load_rag_required(query: str) -> DependencyResult` (in `context.py`) — **[NEW]**
- **Allowed only for**: `project-rag-search`
- **Behaviour**: Initializes and queries RAG, but still targeted to supplied query

### `check_workspace_scan_allowed(skill_name: str, mode: str) -> DependencyResult` (in `context.py`)
- **Behaviour**:
  - If mode is `none` → return `DependencyResult(status="skipped")`
  - If mode is `required` and skill is NOT in `WORKSPACE_SCAN_ALLOWED_SKILLS` → return `DependencyResult(status="blocked", action="block")` and raise `RuntimeError`
- **`WORKSPACE_SCAN_ALLOWED_SKILLS`**: `{"project-memory-bootstrap", "project-memory-update", "project-discovery"}`

### `load_version_cached() -> DependencyResult` (in `context.py`) — **[NEW]**
- **Behaviour**: Reads version from `.agents/state/context.json` → `version` field only
- **Never**: Does NOT scan `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `MANIFEST.json`

### `load_provider_cached() -> DependencyResult` (in `context.py`) — **[NEW]**
- **Behaviour**: Reads provider metadata from `.agents/state/context.json` or `dashboard.json`
- **Never**: Does NOT call provider APIs or run discovery

### `load_usage_cached() -> DependencyResult` (in `context.py`) — **[NEW]**
- **Behaviour**: Reads usage summary from `.agents/state/context/usage.json` or `dashboard.json`
- **Never**: Does NOT parse transcripts or sync request history


---

## 5. Configuration Schema

### `.agents/state/environment.json` (Cache)
```json
{
  "updated_at": "2026-07-10T16:00:00+07:00",
  "tools": {
    "git": {"available": true, "version": "2.45.0"},
    "python": {"available": true, "version": "3.12.4"},
    "node": {"available": true, "version": "20.11.0"},
    "go": {"available": false, "version": null},
    "docker": {"available": false, "version": null},
    "tree-sitter": {"available": false, "version": null},
    "qdrant": {"available": false, "version": null},
    "ollama": {"available": false, "version": null}
  }
}
```

### `.agents/state/runtime/dependencies.json` (Resolution Log)
```json
{
  "skill": "blueprint-to-implementation",
  "resolved_at": "2026-07-10T16:00:00+07:00",
  "requirements": {
    "rules": "required",
    "state": "required",
    "approvals": "required",
    "git": "cached",
    "memory": "lazy",
    "environment": "cached"
  },
  "resolved": {
    "rules": {"status": "loaded", "source": "AI_RULES.md + AGENTS.md + SKILL.md"},
    "state": {"status": "loaded", "source": ".agents/state/context.json"},
    "approvals": {"status": "loaded", "source": ".agents/state/approvals.json"},
    "git": {"status": "cached", "source": ".agents/state/environment.json"},
    "memory": {"status": "deferred", "source": null},
    "environment": {"status": "stale", "source": ".agents/state/environment.json", "action": "warn_only"}
  },
  "missing_required": [],
  "warnings": ["environment snapshot is 26h old. Run /environment-health to refresh."]
}
```

### `runtime_requirements` SKILL.md frontmatter schema (per skill)

**Memory mode semantics** *(patched precise definitions)*:
- `cached` → reads ONLY `memory-state.json` + `memory.config.json` metadata. Never reads `project-summary.md`.
- `lazy` → no load at init; targeted load only when skill calls `load_memory_lazy(query=...)`.
- `required` → allowed only for memory-specific skills; loads `project-summary.md` + named targets.

**RAG mode semantics** *(patched precise definitions)*:
- `cached` → reads RAG metadata/status only; never connects or queries vector DB.
- `lazy` → no load at init; actual query only when skill calls `load_rag_lazy(query=...)`.
- `required` → allowed only for `project-rag-search`; may initialize and query RAG.

**Git allowed commands during init** *(explicit list)*:
- ✅ `git branch --show-current`
- ✅ `git status --short`
- ✅ `git rev-parse --is-inside-work-tree`

**Git FORBIDDEN commands during init**:
- ❌ `git --version`
- ❌ `git describe --tags`
- ❌ `git remote -v`
- ❌ `git fetch`
- ❌ `git tag`

Version/tag detection MUST come from cached `.agents/state/context.json`.

**Extended `runtime_requirements` keys** *(patched v1.2 — replaces `transcript_sync` and `provider_usage`)*:

| Key | Replaces | Semantics |
|---|---|---|
| `version` | — | `cached`: reads from state only; `required`: allowed for release skills only; never scans manifests |
| `provider` | `provider_usage` | `cached`: reads provider metadata from state; `lazy`: load when needed; `optional`: use if available |
| `usage` | `transcript_sync` | `cached`: reads usage summary from `dashboard.json` or `context/usage.json`; `lazy`: may run incremental sync when requested; `required`: allowed for reporting/diagnostic skills only |

> **Hard Rules**:
> - `initialize-workflow` MUST use `version: cached`, `provider: optional`, `usage: cached`
> - `initialize-workflow` MUST NOT perform transcript sync under ANY `usage` mode
> - `transcript_sync` and `provider_usage` keys are **deprecated** — `deps fix` will migrate them automatically

| Skill | rules | state | approvals | git | memory | rag | workspace_scan | environment | version | provider | usage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `initialize-workflow` | required | required | required | cached | cached | cached | none | cached | cached | optional | **cached** |
| `project-memory-bootstrap` | required | required | — | cached | required | optional | required | cached | none | none | none |
| `project-memory-update` | required | required | — | cached | required | optional | lazy | cached | none | none | none |
| `project-rag-search` | required | required | — | — | required | required | lazy | none | none | none | none |
| `brainstorming` | required | required | — | — | cached | optional | none | none | none | none | none |
| `brainstorming-to-plan` | required | required | — | — | lazy | lazy | none | none | none | none | none |
| `plan-to-blueprint` | required | required | — | — | lazy | lazy | none | none | none | none | none |
| `blueprint-to-implementation` | required | required | required | cached | lazy | lazy | none | cached | none | none | none |
| `implementation-to-debug` | required | required | — | cached | optional | optional | none | cached | none | none | none |
| `debug-to-verify` | required | required | required | cached | lazy | optional | none | cached | none | none | none |
| `implementation-to-release` | required | required | required | cached | optional | none | none | cached | required | optional | cached |
| `environment-health` | required | required | — | — | — | — | optional | required | none | none | none |

---

## 6. Database & Storage Design

No new database tables are introduced. The resolver and orchestrator write only to JSON state files:
- `.agents/state/runtime/dependencies.json` — overwritten per skill execution
- `.agents/state/environment.json` — written only by `environment-health`; read-only for all other skills
- `.agents/state/workflow/task_graph.json` — built once before implementation; updated on state transitions
- `.agents/state/workflow/tasks.json` — **source of truth** for task progress; updated atomically on each state transition

### `.agents/state/workflow/task_graph.json` Schema
```json
{
  "feature_id": "FEAT-050",
  "graph_version": "1.0.0",
  "phases": {
    "phase-1": {
      "name": "Lightweight Initialization Boundary",
      "tasks": ["Task 1.1", "Task 1.2", "Task 1.3"],
      "status": "in_progress"
    }
  },
  "tasks": {
    "Task 1.1": {
      "phase_id": "phase-1",
      "dependencies": [],
      "dependents": ["Task 1.2"],
      "state": "completed",
      "required": true,
      "verification_status": "pass"
    },
    "Task 1.2": {
      "phase_id": "phase-1",
      "dependencies": ["Task 1.1"],
      "dependents": ["Task 1.3"],
      "state": "ready",
      "required": true,
      "verification_status": "pending"
    }
  },
  "ready_queue": ["Task 1.2"],
  "blocked_tasks": [],
  "failed_tasks": [],
  "completed_tasks": ["Task 1.1"]
}
```

**Graph rules**:
- Built from `phases[]` + `tasks[]` + `dependencies` in plan JSON before implementation starts
- Validated for cycles (DFS); `CyclicDependencyError` blocks implementation
- Unknown dependency references raise `UnknownDependencyError` and block implementation
- A task cannot enter `running` until all its dependencies are `completed`

### `.agents/state/workflow/tasks.json` Schema (Task Ledger)
```json
{
  "feature_id": "FEAT-050",
  "current_phase": "phase-1",
  "current_task": "Task 1.2",
  "tasks_total": 19,
  "tasks_completed": 1,
  "tasks_incomplete": 18,
  "tasks": {
    "Task 1.1": {
      "phase_id": "phase-1",
      "state": "completed",
      "dependencies": [],
      "read_set": ["skills/initialize-workflow/SKILL.md"],
      "write_set": ["skills/initialize-workflow/SKILL.md"],
      "expected_outputs": ["skills/initialize-workflow/SKILL.md"],
      "verification": ["manual_review"],
      "started_at": "ISO8601",
      "completed_at": "ISO8601",
      "attempt": 1,
      "worker_id": null,
      "lock_ids": [],
      "completion_evidence": {
        "files_changed": ["skills/initialize-workflow/SKILL.md"],
        "tests_passed": [],
        "manual_review": true
      }
    }
  }
}
```

**Ledger rules**:
- `tasks.json` is the **single source of truth** for task progress
- AI messages do NOT count as task completion
- Checkpoint updates do NOT count as task completion
- A task in blueprint but missing from `tasks.json` is a `LedgerConsistencyError`
- A phase cannot complete while any of its tasks is not `completed` in the ledger

---

## 7. Cache Architecture

| Cache | Key / Path | TTL | Invalidation | Owner |
|---|---|---|---|---|
| Environment snapshot | `.agents/state/environment.json` | 24 hours | Manual (`/environment-health`) | `environment-health` skill |
| Work item state | `.agents/state/context.json` → `work_item` | Session | On checkpoint change | `workflow_runtime.py` |
| Project version | `.agents/state/context.json` → `version` | Session | On session restart | `workflow_runtime.py` |
| Git branch/status | `.agents/state/context.json` → `git` | Per-turn | On `do_start` | `workflow_runtime.py` |

**Stale Detection**: Environment snapshot older than 86400 seconds → action = `warn_only` with message directing user to run `/environment-health`.

---

## 8. Error Model

| Exception | Trigger Condition | Recovery | Log Level |
|---|---|---|---|
| `MissingRequiredDependencyError` | A `required` dependency cannot be resolved | Print exact dependency name + suggested fix; `sys.exit(1)` | ERROR |
| `InvalidRequirementsKeyError` | Unknown key in `runtime_requirements` | Print key name + list valid keys; `sys.exit(1)` | ERROR |
| `InvalidRequirementsModeError` | Unknown mode value | Print mode name + list valid modes; `sys.exit(1)` | ERROR |
| `SafetyKeyViolationError` | Safety key (`rules`, `state`, `approvals`) set to `lazy`/`none` | Print violation + force `required`; `sys.exit(1)` | CRITICAL |
| `WorkspaceScanBlockedError` | Skill with `workspace_scan: none` attempts scan | Block; print skill name + constraint; `sys.exit(1)` | ERROR |
| `CyclicDependencyError` | Cycle detected in task dependency graph | Print cycle path; block implementation start | CRITICAL |
| `UnknownDependencyError` | Task dependency references non-existent task | Print bad reference; block implementation start | ERROR |
| `ForbiddenStateTransitionError` | Task state transition not in `ALLOWED_TRANSITIONS` | Print current/target state; `sys.exit(1)` | ERROR |
| `LedgerConsistencyError` | Blueprint task missing from `tasks.json` | Print missing task; block phase start | ERROR |

---

## 9. Skill Integration Contracts

### `initialize-workflow`
- **Before Hooks**: Call `resolve_requirements("initialize-workflow", requirements)` at the very start of initialization.
- **After Hooks**: Write `initialization_summary` to `.agents/state/context.json`.
- **Data Exchanged**: `ResolvedRuntimeContext` stored in session under key `"resolved_dependencies"`.

### `blueprint-to-implementation`
- **Before Hooks**: Call `resolve_requirements("blueprint-to-implementation", requirements)` → validate `approvals.blueprint.approved == true`, else block.
- **Runtime Calls**: Call `load_memory_lazy(query="relevant module")` when memory is needed.

---

## 10. CLI & Runtime Contracts

### `deps inspect --skill <name>`
```
python workflow_runtime.py deps inspect --skill blueprint-to-implementation
```
- **Output**: JSON or table of declared `runtime_requirements` from SKILL.md
- **Exit Codes**: 0 (success), 1 (skill not found)

### `deps resolve --skill <name>`
```
python workflow_runtime.py deps resolve --skill blueprint-to-implementation
```
- **Output**: Resolution status per dependency key; writes `dependencies.json`
- **Exit Codes**: 0 (all required resolved), 1 (missing required dependency)

### `deps validate --skill <name>`
```
python workflow_runtime.py deps validate --skill blueprint-to-implementation
```
- **Output**: Validation result; prints all schema errors and warnings
- **Exit Codes**: 0 (valid), 1 (invalid)

### `deps fix --skill <name>` / `deps fix --all` — **[NEW]**
```
python workflow_runtime.py deps fix --skill initialize-workflow
python workflow_runtime.py deps fix --all
```
- **Purpose**: Auto-add missing `runtime_requirements` template to SKILL.md; migrate deprecated `provider_usage`/`transcript_sync` to `provider`/`usage`; correct safety keys; replace unsafe `workspace_scan: required` on non-allowlisted skills
- **Output**: Diff of proposed changes per file before writing
- **Approval**: Requires explicit approval per Approval Gate Policy BEFORE modifying any file
- **Rules**:
  - MUST NOT silently edit files
  - MUST show all affected files and proposed diffs
  - MUST require user approval before writing
  - After approval, writes changes and runs `deps validate` to confirm fix
- **Exit Codes**: 0 (success or no changes), 1 (approval denied or validation failed)

### `task graph build`
```
python workflow_runtime.py task graph build --feature FEAT-050
```
- **Output**: Builds and writes `.agents/state/workflow/task_graph.json`; prints cycle/consistency errors
- **Must run before**: implementation start
- **Exit Codes**: 0 (graph valid), 1 (cycle or unknown reference found)

### `task graph status`
```
python workflow_runtime.py task graph status
```
- **Output**: Prints current task graph state — ready queue, blocked tasks, completed tasks, phase statuses

### `task state transition <task_id> <new_state>`
```
python workflow_runtime.py task state transition "Task 1.2" running
```
- **Output**: Applies state transition; blocks forbidden transitions; writes updated `tasks.json`
- **Exit Codes**: 0 (success), 1 (forbidden transition)

### `task next`
```
python workflow_runtime.py task next
```
- **Output**: Prints next ready task recommendation with reason
- **Exit Codes**: 0 (recommendation available), 1 (blocked/failed state requires recovery)

### `work-item detect --cached`
```
python workflow_runtime.py work-item detect --cached
```
- **Output**: JSON `{"id": "FEAT-050", "type": "FEAT", "title": "..."}`
- **Never**: Does NOT scan `docs/` directory

### `project version --cached`
```
python workflow_runtime.py project version --cached
```
- **Output**: version string from cached `context.json`
- **Never**: Does NOT read manifest files

### `env snapshot`
```
python workflow_runtime.py env snapshot
```
- **Output**: Runs toolchain checks and writes `.agents/state/environment.json`
- **Note**: This is the ONLY command allowed to run CLI version checks

---

## 11. Sequence Flows

### Normal Lightweight Init Flow
1. `initialize-workflow` SKILL.md instructs: run `deps resolve --skill initialize-workflow`
2. `dependency_resolver.resolve_requirements()` reads `runtime_requirements` from `initialize-workflow/SKILL.md`
3. Resolver loads: `rules` (AI_RULES.md + AGENTS.md), `state` (context.json), `approvals` (approvals.json), `git` (from cache)
4. Resolver checks: `memory → cached` (read metadata only), `environment → cached` (read environment.json, warn if stale)
5. Resolver writes `dependencies.json`
6. Init completes in < 0.8 seconds — no workspace scan, no RAG connect, no toolchain checks

### Missing Required Dependency Flow
1. `blueprint-to-implementation` calls `deps resolve --skill blueprint-to-implementation`
2. Resolver checks `approvals → required`
3. `approvals.json` exists but `blueprint.approved == false`
4. Resolver raises `MissingRequiredDependencyError("approvals.blueprint")`
5. Output: `"Cannot run blueprint-to-implementation. Blueprint is not approved. Run /plan-to-blueprint and have Ba approve it first."`
6. `sys.exit(1)` — skill execution is blocked

### Stale Environment Snapshot Flow
1. Resolver loads `environment → cached`
2. Reads `.agents/state/environment.json`
3. `updated_at` is 30 hours ago (> 24h threshold)
4. Returns `DependencyResult(status="stale", action="warn_only")`
5. Warning printed: `"⚠️ Environment snapshot is 30h old. Run /environment-health to refresh."`
6. Execution continues — environment stale does NOT block

### Lazy Memory Load Flow
1. During skill execution, Coder agent calls `load_memory_lazy(query="auth module design")`
2. `dependency_resolver` checks `memory` mode is `lazy` → allowed
3. Loads only `project-summary.md` and targeted memory chunks
4. Returns loaded content
5. Full `memory-state.json` is never loaded unless explicitly requested

### Phase Completion Gate Flow
1. Task 1.1 completes → `validate_phase_completion("phase-1")` is called
2. Resolver checks: Task 1.2 is still `queued` → Phase 1 is **NOT complete**
3. Task 1.2 completes → `validate_phase_completion("phase-1")` is called again
4. All tasks complete + exit criteria pass → Phase 1 is **complete**
5. Phase 2 begins only after Phase 1 coverage result is `ok=True`

---

## 11b. Visualizer Reader Audit Contract

### Files to Audit
- `extensions/visualizer/src/extension.ts` — may read `.agents/.session.json` directly
- `extensions/visualizer/resources/webview.html` — may read flat `.agents/state/*.json`
- Any generated webview bundle that references session or state paths

### Required Behavior After FEAT-050
- Visualizer MUST prefer `.agents/state/dashboard.json` as the primary state source
- Fallback to deprecated `.agents/.session.json` ONLY with a console warning logged
- Visualizer MUST NOT display `release_allowed=true` if `dashboard.json` contains `release_allowed=false`
- Any direct reads of `.session.json` must be replaced with `dashboard.json` reads

### Audit Acceptance Criteria
- [ ] `extension.ts` does not read `.session.json` without fallback guard
- [ ] `webview.html` reads `dashboard.json` as primary source
- [ ] Release status display is gated on `dashboard.release_allowed`

---

## 12. Security & Safety

- **Workspace Boundary**: `dependency_resolver.py` only reads files within `.agents/` and `skills/` directories. It never writes to source code or arbitrary paths.
- **Safety Key Invariant**: `rules`, `state`, and `approvals` CANNOT be set to `lazy`, `optional`, or `none` by any skill. Validated at `deps validate` time and at `deps resolve` time.
- **Approval Gate Preservation**: `blueprint-to-implementation` always resolves `approvals: required`. The resolver enforces this; it cannot be bypassed by skill configuration.
- **Workspace Scan Gate**: Only `project-memory-bootstrap`, `project-memory-update`, `project-discovery` are in `WORKSPACE_SCAN_ALLOWED_SKILLS`. All other skills receive `WorkspaceScanBlockedError`.
- **Path Validation**: `dependency_resolver.parse_requirements()` only reads from `skills/<skill_name>/SKILL.md`. Input `skill_name` must match `^[a-z0-9-]+$` (regex-validated) to prevent path traversal.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit | `test_dependency_resolver.py` | `load_guardrails_summary()` | Returns hash dict, not full text |
| FR-01 | Unit | `test_dependency_resolver.py` | `load_rules()` | Rules loaded successfully |
| FR-03 | Unit | `test_runtime_requirements_schema.py` | `parse_requirements()` | YAML parsed correctly |
| FR-03 | Unit | `test_runtime_requirements_schema.py` | `validate_requirements()` | Invalid key raises error |
| FR-03 | Unit | `test_runtime_requirements_schema.py` | `validate_requirements()` | Invalid mode raises error |
| FR-03 | Unit | `test_runtime_requirements_schema.py` | `validate_requirements()` | `rules: lazy` → SafetyKeyViolationError |
| FR-04 | Unit | `test_dependency_resolver.py` | `resolve_requirements()` | Required missing → blocks |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_memory_cached()` | Only reads metadata JSONs |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_memory_cached()` | Does NOT read project-summary.md |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_memory_lazy()` | No load with no query |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_memory_lazy()` | Targeted load with query |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_rag_cached()` | Only reads RAG metadata |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_rag_lazy()` | No load with no query |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_usage_cached()` | Does NOT parse transcript |
| FR-06 | Unit | `test_dependency_resolver.py` | `load_version_cached()` | Does NOT scan manifest files |
| FR-05 | Unit | `test_dependency_resolver.py` | `read_environment_snapshot()` | Reads `.json` not CLI |
| FR-05 | Unit | `test_dependency_resolver.py` | `read_environment_snapshot()` | Stale → warn, not block |
| FR-05 | Unit | `test_dependency_resolver.py` | `read_environment_snapshot()` | Missing → warn, not crash |
| FR-07 | Integration | `test_dependency_resolver_cli.py` | `deps doctor` | All skills have manifest |
| FR-07 | Integration | `test_dependency_resolver_cli.py` | `deps doctor` | Legacy skills report warning (not error in non-strict) |
| FR-07 | Integration | `test_dependency_resolver_cli.py` | `deps resolve` | Writes `dependencies.json` |
| Phase | Unit | `test_phase_completion_gate.py` | `validate_phase_completion()` | Phase 1 incomplete with only Task 1.1 done |
| Phase | Unit | `test_phase_completion_gate.py` | `validate_phase_completion()` | Phase 1 complete only when all phase tasks done |
| Phase | Unit | `test_phase_completion_gate.py` | `validate_phase_completion()` | No skipped task passes without approved_skip_reason |
| Graph | Unit | `test_task_dependency_graph.py` | `build_task_graph()` | Task 1.1 complete but 1.2/1.3 incomplete → phase blocked |
| Graph | Unit | `test_task_dependency_graph.py` | `build_task_graph()` | Dependency cycle blocks graph creation |
| Graph | Unit | `test_task_dependency_graph.py` | `build_task_graph()` | Unknown dependency reference blocks graph creation |
| Graph | Unit | `test_task_dependency_graph.py` | `build_task_graph()` | Task cannot run before dependencies complete |
| StateMachine | Unit | `test_task_state_machine.py` | `transition_task_state()` | `queued -> completed` is forbidden |
| StateMachine | Unit | `test_task_state_machine.py` | `transition_task_state()` | `waiting -> completed` is forbidden |
| StateMachine | Unit | `test_task_state_machine.py` | `transition_task_state()` | `running -> queued` is forbidden |
| StateMachine | Unit | `test_task_state_machine.py` | `transition_task_state()` | `completed -> running` without rerun approval is forbidden |
| NextTask | Unit | `test_next_ready_task.py` | `get_next_ready_task()` | After Task 1.1 complete, next is Task 1.2 |
| NextTask | Unit | `test_next_ready_task.py` | `get_next_ready_task()` | Does NOT recommend next phase while current phase incomplete |
| NextTask | Unit | `test_next_ready_task.py` | `get_next_ready_task()` | Does NOT recommend debug while current phase incomplete |
| NextTask | Unit | `test_next_ready_task.py` | `get_next_ready_task()` | Does NOT recommend release before all phases + debug + verify |
| DepsFix | Unit | `test_deps_fix.py` | `deps fix --skill` | Proposes safe runtime_requirements template |
| DepsFix | Unit | `test_deps_fix.py` | `deps fix --all` | Reports all affected SKILL.md files before writing |
| DepsFix | Unit | `test_deps_fix.py` | `deps fix` | Migrates deprecated `transcript_sync` → `usage` |
| DepsFix | Unit | `test_deps_fix.py` | `deps fix` | Migrates deprecated `provider_usage` → `provider` |
| FR-01 | Performance | `test_lightweight_initialize.py` | `do_init` | Completes in < 0.8s |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | `sync_request_history` NOT called |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | `parse_transcript` NOT called |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | `refresh_context_usage_for_active_conversation` NOT called |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | No memory full load triggered |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | No RAG connect triggered |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | No workspace scan triggered |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | No env CLI checks triggered |
| FR-01 | No-Heavy | `test_lightweight_initialize.py` | `do_init` | `git describe --tags` NOT called |
| FR-01 | Compatibility | `test_lightweight_initialize.py` | legacy skill | `safe_minimal` fallback triggers (not full_preload) |
| Safety | Unit | `test_dependency_resolver.py` | `validate_requirements()` | `rules: none` → safety error |
| Safety | Unit | `test_dependency_resolver.py` | `check_workspace_scan_allowed()` | `brainstorming` blocked |
| Safety | Unit | `test_dependency_resolver.py` | `get_doctor_report(strict=True)` | Missing manifest → error |

---

## 14. Requirement Traceability Matrix

| Req ID | Task | Module | File | Test | Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Task 1.1 | `initialize-workflow` | `SKILL.md` | `test_lightweight_initialize.py` | — |
| FR-01 | Task 1.2 | `workflow_runtime` | `workflow_runtime.py` | `test_lightweight_initialize.py` | — |
| FR-02 | Task 1.3 | `validator` | `validator.py` | `test_dependency_resolver.py` | — |
| FR-03 | Task 2.2 | `dependency_resolver` | `dependency_resolver.py` | `test_runtime_requirements_schema.py` | — |
| FR-04 | Task 2.4 | `dependency_resolver` | `dependency_resolver.py` | `test_dependency_resolver.py` | — |
| FR-05 | Task 3.1 | `validator` | `validator.py` | `test_dependency_resolver.py` | — |
| FR-06 | Task 3.2 | `context` | `context.py` | `test_dependency_resolver.py` | — |
| FR-06 | Task 3.3 | `context` | `context.py` | `test_dependency_resolver.py` | — |
| FR-07 | Task 4.1 | All core skills | `*/SKILL.md` | `test_dependency_resolver_cli.py` | — |
| Graph | Task 2.1 | `task_orchestrator` | `task_orchestrator.py` | `test_task_dependency_graph.py` | — |
| StateMachine | Task 2.1 | `task_orchestrator` | `task_orchestrator.py` | `test_task_state_machine.py` | — |
| NextTask | Task 2.1 | `task_orchestrator` | `task_orchestrator.py` | `test_next_ready_task.py` | — |
| DepsFix | Task 2.3 | `workflow_runtime` | `workflow_runtime.py` | `test_deps_fix.py` | — |

---

## 15. File-Level Implementation Contracts

> **Rule**: Every task MUST have a complete implementation contract. If a task is listed in `tasks[]` but has no explicit contract below, the implementer MUST derive read_set, write_set, and verification from the task JSON before starting work. Skipping tasks because the contract is absent is NOT allowed.

- **File**: `skills/workflow-runtime/scripts/dependency_resolver.py` *(Task 2.1, 2.2, 2.5)*
  - **Phase**: Phase 2
  - **Owner**: Coder
  - **Inputs**: SKILL.md YAML frontmatter, `.agents/state/` JSON files
  - **Outputs**: `ResolvedRuntimeContext`, `.agents/state/runtime/dependencies.json`
  - **read_set**: `skills/*/SKILL.md`, `.agents/state/approvals.json`, `.agents/state/context.json`, `.agents/state/environment.json`
  - **write_set**: `.agents/state/runtime/dependencies.json`
  - **expected_outputs**: `skills/workflow-runtime/scripts/dependency_resolver.py`
  - **task_state_inputs**: `["queued"]` → `ready` after Task 1.3 complete
  - **task_state_outputs**: `running` → `completed` after tests pass
  - **Implementation Notes**: Pure Python stdlib only. YAML frontmatter parsed with string split on first `---` pair only. `legacy_skill_fallback` = `safe_minimal` (NOT `full_preload`). Includes `validate_phase_completion()`, `get_doctor_report(strict_mode)`, `get_next_ready_task()`. `transcript_sync` and `provider_usage` keys deprecated; `deps fix` auto-migrates them.
  - **Rollback**: `git rm dependency_resolver.py` and revert `do_start` hook in `workflow_runtime.py`
  - **Verification**: `pytest test_dependency_resolver.py test_runtime_requirements_schema.py`

- **File**: `skills/workflow-runtime/scripts/task_orchestrator.py` *(Task 2.1 extension)*
  - **Phase**: Phase 2
  - **Owner**: Coder
  - **Inputs**: Plan JSON, `.agents/state/workflow/task_graph.json`, `.agents/state/workflow/tasks.json`
  - **Outputs**: `task_graph.json`, `tasks.json`
  - **read_set**: `docs/plans/FEAT-050_lightweight_runtime_initialization_plan.json`
  - **write_set**: `.agents/state/workflow/task_graph.json`, `.agents/state/workflow/tasks.json`
  - **expected_outputs**: Both JSON state files created; graph cycle-free and consistent
  - **task_state_inputs**: `queued` → `ready` parallel to `dependency_resolver.py`
  - **task_state_outputs**: `running` → `completed` after graph validated and tests pass
  - **Implementation Notes**:
    - `build_task_graph()`: DFS cycle check; `CyclicDependencyError` on cycle; `UnknownDependencyError` on bad reference
    - `transition_task_state()`: enforces `ALLOWED_TRANSITIONS`; raises `ForbiddenStateTransitionError` on forbidden shortcuts
    - `completed` state requires: implementation done + expected outputs exist + verification passes + no active worker + no active lock
    - `get_next_ready_task()`: uses priority rules — running > failed > ready queue > phase > phases > debug (never release prematurely)
  - **Rollback**: `git rm task_orchestrator.py`; delete `.agents/state/workflow/` directory
  - **Verification**: `pytest test_task_dependency_graph.py test_task_state_machine.py test_next_ready_task.py`

- **File**: `skills/workflow-runtime/scripts/workflow_runtime.py` *(Task 1.2, 2.3, 2.4, 4.3)*
  - **Phase**: Phase 1 & 2 & 4
  - **Owner**: Coder
  - **Inputs**: CLI args, `dependency_resolver.py`, `task_orchestrator.py`
  - **Outputs**: Console output, session state
  - **read_set**: Session JSON files, plan JSON
  - **write_set**: `.agents/state/` JSON files, `tasks.json`, `task_graph.json`
  - **expected_outputs**: `deps` subcommand group works; `task` subcommand group works
  - **task_state_inputs**: `waiting` → `ready` after Task 2.1 complete
  - **task_state_outputs**: `running` → `completed` after CLI tests pass
  - **Implementation Notes**:
    - `update_context_health()` MUST NOT call `get_memory_info()`, `get_rag_info()`, `sync_request_history()`, `parse_transcript()`, or `refresh_context_usage_for_active_conversation()` during `initialize-workflow` execution.
    - `sync_request_history()` guarded: only when `usage: required` in resolved context.
    - `do_start()` calls `resolve_requirements()` then `build_task_graph()` (if not exists) before updating session.
    - Git checks limited to allowed 3 commands. `git describe --tags` REMOVED.
    - `deps` subparser: `inspect`, `resolve`, `validate`, `doctor`, `fix` subcommands.
    - `task` subparser: `graph build`, `graph status`, `state transition`, `next` subcommands.
    - `env snapshot` is ONLY path that may run CLI version checks.
  - **Rollback**: `git revert` the specific commits for `do_start` hook, `deps`, and `task` subparsers
  - **Verification**: `pytest test_dependency_resolver_cli.py test_lightweight_initialize.py test_deps_fix.py`

- **File**: `skills/workflow-runtime/scripts/validator.py` *(Task 1.3, 3.1, 3.4)*
  - **Phase**: Phase 1 & 3
  - **Owner**: Coder
  - **Inputs**: `.agents/state/environment.json`, `.agents/state/context.json`
  - **Outputs**: `DependencyResult` structs
  - **read_set**: `.agents/state/environment.json`, `.agents/state/context.json`
  - **write_set**: None
  - **expected_outputs**: `read_environment_snapshot()`, `detect_work_item_cached()`, `detect_project_version_cached()` functions present
  - **task_state_inputs**: `waiting` → `ready` after Task 1.2 complete
  - **task_state_outputs**: `running` → `completed` after unit tests pass
  - **Implementation Notes**:
    - `get_git_info()`: `git rev-parse --is-inside-work-tree` + `git branch --show-current` + `git status --short` ONLY. Drops `git describe --tags`.
    - `get_version_info()` replaced by `detect_project_version_cached()`.
    - `read_environment_snapshot()`: reads `environment.json`; stale > 24h → `warn_only`; missing → `warn_only`.
    - `detect_work_item_cached()`: reads `context.json`. NEVER scans `docs/`.
  - **Rollback**: `git revert` validator.py; restore original functions
  - **Verification**: `pytest test_dependency_resolver.py -k env_snapshot`

- **File**: `skills/workflow-runtime/scripts/context.py` *(Task 3.2, 3.3, 3.5)*
  - **Phase**: Phase 3
  - **Owner**: Coder
  - **Inputs**: resolved dependency mode flags from session
  - **Outputs**: Loaded resource content or deferred handles
  - **read_set**: `.agents/memory/`, `.agents/rag/`, `.agents/state/context.json`
  - **write_set**: None (read-only lazy loaders)
  - **expected_outputs**: All 8 new load functions present and tested
  - **task_state_inputs**: All 3.x tasks can run in parallel after Task 2.5
  - **task_state_outputs**: Each task `running` → `completed` after its unit tests pass
  - **Implementation Notes**:
    - `load_memory_cached()`: reads ONLY `memory-state.json` + `memory.config.json`.
    - `load_memory_lazy(query=None)`: deferred; targeted chunks only when query supplied.
    - `load_memory_required(targets)`: ONLY for `project-memory-bootstrap`, `project-memory-update`.
    - `load_rag_cached()`: reads RAG metadata only; no vector DB connection.
    - `load_rag_lazy(query=None)`: deferred; RAG query only when query supplied.
    - `load_version_cached()`: reads version from `context.json` only; never scans manifests.
    - `load_provider_cached()`: reads provider metadata from `context.json` or `dashboard.json`.
    - `load_usage_cached()`: reads usage summary from `context/usage.json` or `dashboard.json`; NEVER parses transcripts.
    - `check_workspace_scan_allowed()`: enforces `WORKSPACE_SCAN_ALLOWED_SKILLS` gate.
  - **Rollback**: `git revert` context.py
  - **Verification**: `pytest test_dependency_resolver.py -k memory_or_rag`

- **File**: `skills/workflow-runtime/scripts/session.py` *(Task 1.3)*
  - **Phase**: Phase 1
  - **Owner**: Coder
  - **read_set**: `AI_RULES.md`, `AGENTS.md`, active SKILL.md, `.agents/state/approvals.json`, `.agents/state/dashboard.json`
  - **write_set**: None (read-only)
  - **expected_outputs**: `load_guardrails_summary()`, `load_approval_state()`, `load_dashboard_state()` present
  - **task_state_inputs**: `waiting` → `ready` after Task 1.2
  - **task_state_outputs**: `running` → `completed` after tests pass
  - **Implementation Notes**:
    - `load_guardrails_summary()`: SHA-256 hash of rules files; returns `policy_flags` dict.
    - `load_approval_state()`: reads `.agents/state/approvals.json`.
    - `load_dashboard_state()`: reads `.agents/state/dashboard.json`.
  - **Rollback**: `git revert` session.py
  - **Verification**: `pytest test_dependency_resolver.py -k guardrails`

- **File**: `skills/workflow-runtime/scripts/state_sync.py` *(Task 1.3)*
  - **Phase**: Phase 1
  - **Owner**: Coder
  - **read_set**: session dict
  - **write_set**: `.agents/state/context.json`
  - **expected_outputs**: `write_initialization_summary()`, `validate_no_heavy_init_operations()` present
  - **task_state_inputs**: `waiting` → `ready` after Task 1.2
  - **task_state_outputs**: `running` → `completed`
  - **Implementation Notes**:
    - `write_initialization_summary()`: writes lightweight summary (guardrail hashes, git, checkpoint).
    - `validate_no_heavy_init_operations()`: checks session flags — no memory/RAG/transcript during init.
  - **Rollback**: `git revert` state_sync.py
  - **Verification**: Manual + `test_lightweight_initialize.py`

- **File**: `skills/initialize-workflow/SKILL.md` *(Task 1.1)*
  - **Phase**: Phase 1
  - **Owner**: Architect
  - **read_set**: `skills/initialize-workflow/SKILL.md`
  - **write_set**: `skills/initialize-workflow/SKILL.md`
  - **expected_outputs**: Updated SKILL.md with no forbidden operations
  - **task_state_inputs**: `queued` → `ready` (no dependencies)
  - **task_state_outputs**: `running` → `completed` after manual review
  - **Implementation Notes**: Steps: `deps resolve` → guardrails summary → git (3 allowed cmds) → cached state+approvals → write summary. STOP.
  - **Rollback**: `git revert` SKILL.md
  - **Verification**: Manual review — confirm no forbidden operations

- **File**: `skills/workflow-runtime/tests/test_lightweight_initialize.py` *(Task 5.2, 5.3)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **read_set**: `workflow_runtime.py`, `context.py`
  - **write_set**: `skills/workflow-runtime/tests/test_lightweight_initialize.py`
  - **expected_outputs**: All 8 no-heavy-init mock assertions + latency assertion
  - **task_state_inputs**: `waiting` → `ready` after Task 4.3
  - **Implementation Notes**: See test matrix above for complete assertion list.
  - **Rollback**: Delete test file
  - **Verification**: `pytest test_lightweight_initialize.py -v`

- **File**: `skills/workflow-runtime/tests/test_phase_completion_gate.py` *(Task 5.1)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **read_set**: `dependency_resolver.py`, `task_orchestrator.py`
  - **write_set**: `skills/workflow-runtime/tests/test_phase_completion_gate.py`
  - **expected_outputs**: Phase gate tests + ledger consistency tests
  - **Implementation Notes**:
    - Task 1.1 only complete → `validate_phase_completion("phase-1")` returns `ok=False`
    - All Phase 1 tasks complete → returns `ok=True`
    - Task blocked → `ok=False` with `incomplete_tasks` listing it
  - **Rollback**: Delete test file
  - **Verification**: `pytest test_phase_completion_gate.py -v`

- **File**: `skills/workflow-runtime/tests/test_task_dependency_graph.py` *(Task 5.1)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **expected_outputs**: 5 graph validation test cases
  - **Implementation Notes**: Cycle detection; unknown ref; dependency ordering; graph JSON output
  - **Verification**: `pytest test_task_dependency_graph.py -v`

- **File**: `skills/workflow-runtime/tests/test_task_state_machine.py` *(Task 5.1)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **expected_outputs**: All forbidden transitions raise `ForbiddenStateTransitionError`; all allowed transitions succeed
  - **Verification**: `pytest test_task_state_machine.py -v`

- **File**: `skills/workflow-runtime/tests/test_next_ready_task.py` *(Task 5.1)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **expected_outputs**: 4 recommendation scenarios tested
  - **Verification**: `pytest test_next_ready_task.py -v`

- **File**: `skills/workflow-runtime/tests/test_deps_fix.py` *(Task 5.1)*
  - **Phase**: Phase 5
  - **Owner**: Reviewer
  - **expected_outputs**: 4 `deps fix` test scenarios including deprecation migration
  - **Verification**: `pytest test_deps_fix.py -v`

---

## 16. Acceptance Criteria

The blueprint is **approved only if** all of the following hold:

- [ ] Task dependency graph (`task_graph.json`) exists and is cycle-validated before implementation
- [ ] Task state machine blocks all invalid transitions (9 forbidden shortcuts enforced)
- [ ] Phase completion requires ALL phase tasks to be `completed` with verification `pass`
- [ ] `get_next_ready_task()` recommends next task, not next phase, while current phase is incomplete
- [ ] No phase can complete after only the first blocking task in that phase
- [ ] `runtime_requirements` supports `version`, `provider`, `usage` keys (replacing `transcript_sync`, `provider_usage`)
- [ ] `deps fix` is defined with approval gate and diff output before writing
- [ ] `initialize-workflow` declares `version: cached`, `provider: optional`, `usage: cached` and does NOT perform transcript sync
- [ ] `legacy_skill_fallback` is `safe_minimal` — NOT `full_preload`
- [ ] Tests cover: task graph (5 cases), state machine (4 forbidden + allowed), next task (4 scenarios), deps fix (4 cases), no-heavy-init (8 mocks), phase gate (3 cases)
- [ ] Every task in the blueprint has a complete implementation contract with `phase_id`, `read_set`, `write_set`, `expected_outputs`, `task_state_inputs`, `task_state_outputs`, `verification`, `rollback`
