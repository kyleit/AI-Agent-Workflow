<!-- File path: docs/designs/FEAT-063_vir_multi_agent_consensus_blueprint.md -->

---
feature_id: FEAT-063
feature_name: Visual Intelligence Runtime — Multi-Agent Architecture & Consensus Engine
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-063_vir_multi_agent_consensus_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Multi-Agent Architecture & Consensus Engine

## 0. Baseline Context & References
- **Memory Baseline**: Memory of agent status bindings and SQLite schema configurations.
- **RAG Query Summaries**: The Consensus Engine subscribes to sensory evidence topics via `AsyncEventBus` and logs results to `vir_evidence` tables.
- **Inspected Source Files**:
  - [FEAT-063 Plan](file:///e:/AgentsProject/docs/plans/FEAT-063_vir_multi_agent_consensus_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/multi_agent/contract.py` | Create | Define base Agent Contracts Protocol interface | None | High. Backbone of agent registration specs. |
| `vir_runtime/multi_agent/registry.py` | Modify | Implement agent lifecycle states, subscriptions, and validations | `contract.py` | High. Controls active agent collections. |
| `vir_runtime/multi_agent/consensus.py` | Create | Compute weighted authority scoring and resolve VETOs | `registry.py` | High. Final quality decision algorithms. |
| `vir_runtime/multi_agent/config.py` | Create | Load domain authority weights and thresholds from `vir_agents.yaml` | None | Low. Handles static settings variables. |
| `vir_runtime/multi_agent/protocol.py` | Create | Define inter-agent message formats and age filters | None | Medium. Messaging specifications. |
| `vir_runtime/multi_agent/memory.py` | Create | Manage the 5 layers of agent memory data structures | None | Medium. Controls agent SQLite access. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── multi_agent/
    ├── config.py
    ├── consensus.py
    ├── contract.py
    ├── memory.py
    ├── protocol.py
    └── registry.py
```

---

## 3. Complete Class & Module Design

### 3.1 AgentContract (Protocol)
- **Class / Module Name**: `vir_runtime.multi_agent.contract.AgentContract`
  - **Responsibilities**: Declare interface specifications for all agents.
  - **Public Methods**:
    - `async def initialize() -> None`
    - `async def handle_message(msg: AgentMessage) -> None`
    - `def get_contract_details() -> Dict[str, Any]`

### 3.2 ConsensusEngine
- **Class / Module Name**: `vir_runtime.multi_agent.consensus.ConsensusEngine`
  - **Responsibilities**: Load active votes, evaluate weighted authority scores, check VETO credentials, and output `ConsensusRecord` objects.
  - **Constructor Parameters**:
    - `bus: AsyncEventBus`
  - **Public Methods**:
    - `async def collect_votes() -> ConsensusRecord`
    - `def register_vote(agent_name: str, vote: Dict[str, Any]) -> None`
  - **Dependencies**: `vir_runtime.multi_agent.config`

### 3.3 AgentMemory
- **Class / Module Name**: `vir_runtime.multi_agent.memory.AgentMemory`
  - **Responsibilities**: Abstract SQLite (long-term), RAM (short-term/working), and Event Bus (shared) writes.
  - **Constructor Parameters**:
    - `agent_id: str`
    - `db_path: str`
  - **Public Methods**:
    - `def write_short_term(key: str, value: Any) -> None`
    - `async def save_long_term(entity: str, pattern: str) -> None`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def collect_votes() -> ConsensusRecord`
  - **Parameters**: None.
  - **Return Types**: Returns a `ConsensusRecord` instance.
  - **Exceptions**:
    - `ConsensusExecutionTimeoutError` - If collection waits exceed timeouts.

---

## 5. Configuration Schema

- **Target Schema (`vir_agents.yaml`)**:
```yaml
consensus:
  confidence_threshold: 0.85
  domain_weights:
    design: 1.0
    accessibility: 1.0
    performance: 0.7
    network: 0.8
```

---

## 6. Database & Storage Design
- **Tables**:
  - `vir_agent_memory`:
    - `agent_id` (TEXT)
    - `key` (TEXT)
    - `value` (TEXT, JSON string)
    - `updated_at` (TEXT)

---

## 7. Cache Architecture
- **Agent Message Cache**:
  - Memory list stores processed message IDs to drop duplicates.

---

## 8. Error Model

- **Exception Class**: `ConsensusExecutionTimeoutError`
  - **Trigger Condition**: Agents fail to return decisions within limits.
  - **Recovery Strategy**: Degrade missing votes to `ABSTAIN`, calculate scores with active votes.
  - **Logging Requirements**: WARNING log highlighting slow agent names.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Consensus Decision Flow**:
  1. Observers post findings to bus.
  2. Agents publish votes to `ConsensusEngine`.
  3. Design agent submits `VETO` event with evidence uuid link.
  4. Consensus Engine processes veto weights.
  5. PASS blocked; verdict resolved as `FAIL`.
  6. Final record posted on `vir.consensus.verdict`.

---

## 12. Security & Safety
- **Veto Evidence Guard**: The Consensus Engine checks that any active `VETO` event has >= 1 linked `Evidence` object, downgrading unverified vetoes to `ADVISORY` warnings.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-06` | Unit Test | `tests/unit/test_weighted_consensus.py` | `consensus.py` | `self.assertEqual(record.verdict, "FAIL")` |
| `FR-09` | Unit Test | `tests/unit/test_unsupported_veto.py` | `consensus.py` | `self.assertEqual(record.verdict, "PASS")` |

---

## 14. Requirement Traceability Matrix
- `FR-06` -> Task 1.5 -> Class `ConsensusEngine` -> `consensus.py` -> `test_weighted_consensus.py` -> Verified.
- `FR-09` -> Task 1.8 -> Class `ConsensusEngine` -> `consensus.py` -> `test_unsupported_veto.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/multi_agent/consensus.py`
  - **Purpose**: Multi-agent consensus voting engine.
  - **Owner**: Architect
  - **Inputs / Outputs / Dependencies**: Depends on weights loaded from `config.py`.
