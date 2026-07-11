<!-- File path: docs/designs/FEAT-055_vir_vision_goals_and_architectural_foundation_blueprint.md -->

---
feature_id: FEAT-055
feature_name: Visual Intelligence Runtime — Vision, Goals & Architectural Foundation
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-055_vir_vision_goals_and_architectural_foundation_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Visual Intelligence Runtime (VIR) Foundation

## 0. Baseline Context & References
- **Memory Baseline**: Subsystem configuration registry loaded from `.agents/visual-runtime/` workspace setup context.
- **RAG Query Summaries**: `project-profile.json` structure analyzed; interfaces align with Knowledge Runtime requirements.
- **Inspected Source Files**:
  - [FEAT-055 Plan](file:///e:/AgentsProject/docs/plans/FEAT-055_vir_vision_goals_and_architectural_foundation_plan.md)
  - [ADR-006 asyncio message bus](file:///e:/AgentsProject/docs/adr/ADR-006_asyncio_local_message_bus.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/core/runtime.py` | Create | Initialize core runtime instance and bootstrap settings | None | Low. Entry point of the entire runtime. |
| `vir_runtime/core/orchestrator.py` | Create | Manage the perception-first pipeline flow loops | `runtime.py` | High. Controls execution stages transitions. |
| `vir_runtime/domain/twin.py` | Create | Define structural schemas representing the 11 twin dimensions | None | Medium. Basis for all state consistency checks. |
| `vir_runtime/core/execution.py` | Create | Manage parameters for the 4 execution modes | `runtime.py` | Low. Configures platform interfaces. |
| `vir_runtime/core/profiles.py` | Create | Activating specific agent sets per selected profile | `runtime.py` | Low. Loads profile settings maps. |
| `vir_runtime/adapters/base/interface.py` | Create | Define base Protocols for all provider adapters | None | High. All external libraries wrap these types. |
| `.agents/skills/frontend-visual-debug/SKILL.md` | Modify | Simplify skill internals to delegate calls to VIR CLI | `runtime.py` | Medium. Refactors old skill into thin client. |
| `vir_runtime/domain/agent_contract.py` | Create | Define validation interfaces for agent registrations | None | Medium. Enforces agent structures compliance. |

---

## 2. Target Folder Structure
```text
vir_runtime/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── execution.py
│   ├── orchestrator.py
│   ├── profiles.py
│   └── runtime.py
├── domain/
│   ├── __init__.py
│   ├── agent_contract.py
│   └── twin.py
└── adapters/
    ├── __init__.py
    └── base/
        ├── __init__.py
        └── interface.py
```

---

## 3. Complete Class & Module Design

### 3.1 VIRRuntimeCore
- **Class / Module Name**: `vir_runtime.core.runtime.VIRRuntimeCore`
  - **Responsibilities**: Load system configurations, initialize adapters base classes, check workspace constraints.
  - **Constructor Parameters**:
    - `config_path: str` - Path to local configs overrides.
  - **Public Methods**:
    - `async def bootstrap() -> None` - Loads modules settings, registries.
    - `async def shutdown() -> None` - Closes active DB pools and releases files.
  - **Internal Methods**:
    - `def _load_env() -> None` - Configures environment parameters.
  - **Dependencies**: `vir_runtime.core.config`, `vir_runtime.adapters.registry`

### 3.2 LifecycleOrchestrator
- **Class / Module Name**: `vir_runtime.core.orchestrator.LifecycleOrchestrator`
  - **Responsibilities**: Move through the perception loop (Observe, Understand, Reason, Investigate, Learn, Improve) sequentially.
  - **Constructor Parameters**:
    - `runtime: VIRRuntimeCore` - Parent core context instance.
  - **Public Methods**:
    - `async def execute_run(url: str, profile_name: str) -> str` - Triggers the pipeline loop.
  - **Internal Methods**:
    - `async def _transition_stage(target_stage: str) -> None` - Triggers state updates and logs.
  - **Dependencies**: `vir_runtime.core.profiles`

---

## 4. Detailed Interface Contracts

- **API Signature**: `def execute_run(url: str, profile_name: str) -> str`
  - **Parameters**:
    - `url` (valid URL formats, no defaults)
    - `profile_name` (`lightweight`, `standard`, or `deep`)
  - **Return Types**: Returns a string file path pointing to the generated MD verification report.
  - **Exceptions**:
    - `InvalidProfileError` - Thrown if profile name is unmapped.
    - `BootstrappingFailedError` - Thrown if database connection fails at start.

---

## 5. Configuration Schema

- **Current Schema**: None (pre-foundation).
- **Target Schema**:
```yaml
vir:
  version: "1.0.0"
  profile: "standard"
  database:
    sqlite_path: ".agents/visual-runtime/vir_state.db"
  profiles:
    lightweight:
      timeout_seconds: 5
      active_agents: ["dom_inspector"]
    standard:
      timeout_seconds: 30
      active_agents: ["dom_inspector", "pixel_comparer", "console_monitor"]
```

---

## 6. Database & Storage Design
- **Tables**:
  - `vir_session`:
    - `session_id` (TEXT, Primary Key, UUID)
    - `created_at` (TEXT, ISO-8601)
    - `status` (TEXT, e.g. "ACTIVE", "COMPLETED")
- **Indexes**: None for MVP session tables.
- **Migration Strategy**: SQLite creation commands run automatically if the file does not exist during `bootstrap()`.

---

## 7. Cache Architecture
- No caching is defined for the foundation layout. (Deferred to sensory and memory phases).

---

## 8. Error Model

- **Exception Class**: `VIRRuntimeError`
  - **Trigger Condition**: General runtime faults during startup or pipeline execution.
  - **Recovery Strategy**: Force exit with code 1 in CLI mode, cleanup open file descriptors.
  - **Logging Requirements**: ERROR level logs containing traceback strings.

---

## 9. Skill Integration Contracts
- **Skill Name**: `frontend-visual-debug`
  - **Before Hooks**: Validates that target port is open.
  - **After Hooks**: Formats Markdown outputs logs.
  - **Runtime Calls**: Runs `python -m vir_runtime.core.runtime --url <URL>` via subprocess.

---

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python -m vir_runtime.core.runtime --url <URL> --profile <PROFILE>`
  - **Parameters**:
    - `--url` (Target endpoint url)
    - `--profile` (lightweight | standard | deep)
  - **Exit Codes**:
    - `0` - PASS or PARTIAL PASS
    - `1` - FAIL
    - `2` - BLOCKED

---

## 11. Sequence Flows

- **Normal Execution Flow**:
  1. Client invokes thin client SKILL.md.
  2. Subprocess starts `VIRRuntimeCore.bootstrap()`.
  3. `LifecycleOrchestrator` runs stages: Observe -> Understand -> Reason -> Investigate -> Learn -> Improve.
  4. Output report path returned to client.

---

## 12. Security & Safety
- **Workspace Boundary**: The execution script strictly restricts file write targets within `.agents/visual-runtime/`.
- **Path Validation**: Rejects parameters containing path escapes like `../`.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_runtime_init.py` | `runtime.py` | `self.assertIsNotNone(core)` |
| `FR-05` | Unit Test | `tests/unit/test_profiles_mapping.py` | `profiles.py` | `self.assertEqual(len(active_agents), 3)` |
| `FR-07` | Integration Test | `tests/integration/test_thin_client_delegation.py` | `SKILL.md` | `self.assertTrue(report_path.exists())` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `VIRRuntimeCore` -> `runtime.py` -> `test_runtime_init.py` -> Verified.
- `FR-05` -> Task 1.5 -> Class `ProfileManager` -> `profiles.py` -> `test_profiles_mapping.py` -> Verified.
- `FR-07` -> Task 1.7 -> Skill wrapper -> `SKILL.md` -> `test_thin_client_delegation.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/core/runtime.py`
  - **Purpose**: Bootstrap settings n-type loader context.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on environment loaders configurations.
