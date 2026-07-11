<!-- File path: docs/designs/FEAT-069_vir_sdlc_integration_blueprint.md -->

---
feature_id: FEAT-069
feature_name: Visual Intelligence Runtime — SDLC Integration & Future AI Capabilities Roadmap
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-069_vir_sdlc_integration_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – SDLC Integration & Future AI Roadmap

## 0. Baseline Context & References
- **Memory Baseline**: Memory of workflow runtime session models and cloud adapter connections parameters.
- **RAG Query Summaries**: SDLC checkpoint manager queries local `.session.json` state indices and updates validation targets dynamically.
- **Inspected Source Files**:
  - [FEAT-069 Plan](file:///e:/AgentsProject/docs/plans/FEAT-069_vir_sdlc_integration_plan.md)
  - [Workflow script](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/workflow_runtime.py)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Bind VIR run verification audits at the 4 checkpoints | `vir_runtime/core/cli.py` | High. Modifies core workflow runner. |
| `.agents/skills/workflow-runtime/scripts/session.py` | MODIFY | Implement validation blockers on session.proceed transitions | None | High. Restricts approval gates blocks. |
| `vir_runtime/core/consent.py` | Create | Intercept cloud API calls, checking user consent overrides | None | Medium. Enforces user privacy checks. |
| `.agents/skills/implementation-to-debug/SKILL.md` | MODIFY | Trigger VIR Standard profile run during debugging pipelines | `workflow_runtime.py` | Low. Enhances debugging skills. |
| `.agents/skills/implementation-to-release/SKILL.md` | MODIFY | Enforce mandatory VIR CI mode validation before package publish | `workflow_runtime.py` | Medium. Release gate enforcer. |
| `vir_runtime/adapters/vision/ollama.py` | Create | Local vision adapter routing queries to Ollama server APIs | None | Medium. Local VLM provider. |
| `vir_runtime/adapters/vision/gemini.py` | Create | Cloud vision adapter routing queries to Gemini API endpoints | None | High. Cloud VLM provider. |

---

## 2. Target Folder Structure
```text
.agents/
└── skills/
    ├── implementation-to-debug/
    │   └── SKILL.md
    ├── implementation-to-release/
    │   └── SKILL.md
    └── workflow-runtime/
        └── scripts/
            ├── session.py
            └── workflow_runtime.py
vir_runtime/
├── adapters/
│   └── vision/
│       ├── gemini.py
│       └── ollama.py
└── core/
    └── consent.py
```

---

## 3. Complete Class & Module Design

### 3.1 SDLCCheckpointManager
- **Class / Module Name**: `vir_runtime.core.consent.SDLCCheckpointManager`
  - **Responsibilities**: Load `.session.json` parameters, evaluate gate states, block manual proceed actions if VIR checks are failed, update active indexes.
  - **Constructor Parameters**:
    - `session_path: str`
  - **Public Methods**:
    - `def verify_gate_block(checkpoint_id: str) -> bool`
    - `def advance_checkpoint() -> None`

### 3.2 ConsentValidator
- **Class / Module Name**: `vir_runtime.core.consent.ConsentValidator`
  - **Responsibilities**: Enforce user approval rules. Read `adapters.yaml`, throwing error if cloud VLM has `consent: false`.
  - **Constructor Parameters**:
    - `config_path: str`
  - **Public Methods**:
    - `def check_consent_permission(provider: str) -> None`

---

## 4. Detailed Interface Contracts

- **API Signature**: `def check_consent_permission(provider: str) -> None`
  - **Parameters**:
    - `provider` (string provider name e.g. `gemini` or `gpt-4v`)
  - **Return Types**: None.
  - **Exceptions**:
    - `ConsentDeniedError` - Thrown if provider requires consent but override flag is false.

---

## 5. Configuration Schema

- **Target Schema (`adapters.yaml` updates)**:
```yaml
adapters:
  vision_providers:
    gemini:
      api_key_env: "GEMINI_API_KEY"
      privacy_level: "cloud"
      cost_tier: "medium"
      consent_required: true
```

---

## 6. Database & Storage Design
- Checkpoint transition histories and audit logs are recorded in the `vir_sessions` SQLite tables.

---

## 7. Cache Architecture
- No cache mechanisms defined.

---

## 8. Error Model

- **Exception Class**: `ConsentDeniedError`
  - **Trigger Condition**: VLM cloud provider query executes without human consent authorization.
  - **Recovery Strategy**: Fail target execution, abort observation loop immediately.
  - **Logging Requirements**: ERROR log stating the target provider name.

---

## 9. Skill Integration Contracts
- **Skill Name**: `workflow-runtime`
  - **Before Hooks**: Runs consent check sweeps before initializing cloud sensory modules.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **SDLC Checkpoint Integration Flow**:
  1. Coder agent completes code changes, calling `workflow_runtime validate`.
  2. Validator calls `CLIRunner` triggering standard audit.
  3. Gate evaluates verification result.
  4. Result is PASS.
  5. `SDLCCheckpointManager` updates `.session.json` active checkpoint parameters.
  6. Proceed gate unlocked; developer proceeds.

---

## 12. Security & Safety
- **Core Isolation Safety**: Future AI adapters registration is limited to vision adapter inheritance classes, preventing modules edits from altering core Event Bus routing structures.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-02` | Unit Test | `tests/integration/test_approval_gate_block.py` | `session.py` | `self.assertTrue(is_blocked)` |
| `FR-22` | Unit Test | `tests/unit/test_cloud_consent.py` | `consent.py` | `self.assertRaises(ConsentDeniedError)` |

---

## 14. Requirement Traceability Matrix
- `FR-02` -> Task 1.2 -> Class `SDLCCheckpointManager` -> `session.py` -> `test_approval_gate_block.py` -> Verified.
- `FR-22` -> Task 1.11 -> Class `ConsentValidator` -> `consent.py` -> `test_cloud_consent.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/adapters/vision/gemini.py`
  - **Purpose**: Connect Gemini API client.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on standard Google GenerativeAI API packages.
