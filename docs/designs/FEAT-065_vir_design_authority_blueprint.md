<!-- File path: docs/designs/FEAT-065_vir_design_authority_blueprint.md -->

---
feature_id: FEAT-065
feature_name: Visual Intelligence Runtime — Design Authority & Design Knowledge Base
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-065_vir_design_authority_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Design Authority & Design Knowledge Base

## 0. Baseline Context & References
- **Memory Baseline**: Memory of Figma layout constraints and hex-to-rgb transformation models.
- **RAG Query Summaries**: Design Authority Agent subscribes to `vir.evidence.new` on `AsyncEventBus` and logs results to `vir_evidence` tables.
- **Inspected Source Files**:
  - [FEAT-065 Plan](file:///e:/AgentsProject/docs/plans/FEAT-065_vir_design_authority_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `.agents/visual-runtime/design-kb/rules.yaml` | Create | Configure baseline typography, colors, and layout rules schemas | None | Medium. Design rules specifications. |
| `.agents/visual-runtime/design-kb/tokens.json` | Create | Define base design token variables (spacing dimensions, grids) | None | Low. Static design system variables. |
| `vir_runtime/design/kb.py` | Create | Provide query lookup APIs for rules and overrides configuration files | None | Medium. Main DB lookup library. |
| `vir_runtime/design/agent.py` | Create | Design Authority Agent executing design audits loops | `kb.py` | High. Evaluates design compliance. |
| `vir_runtime/domain/design_finding.py` | Create | Dataclass representing design system anomalies (`Evidence` subclass) | None | Low. Specialized evidence properties. |
| `vir_runtime/design/veto.py` | Create | Logic allocating VETOs for MUST failures and WARNs for SHOULD ones | `agent.py` | High. Manages decision impacts. |
| `vir_runtime/design/overrides.py` | Create | Load local project-specific design system overrides files | `kb.py` | Low. Customization loader hook. |

---

## 2. Target Folder Structure
```text
.agents/
└── visual-runtime/
    └── design-kb/
        ├── rules.yaml
        └── tokens.json
vir_runtime/
├── design/
│   ├── agent.py
│   ├── kb.py
│   ├── overrides.py
│   └── veto.py
└── domain/
    └── design_finding.py
```

---

## 3. Complete Class & Module Design

### 3.1 DesignKnowledgeBase
- **Class / Module Name**: `vir_runtime.design.kb.DesignKnowledgeBase`
  - **Responsibilities**: Parse rules and token definitions from YAML/JSON files, load local custom project-specific overrides.
  - **Constructor Parameters**:
    - `kb_dir: str`
  - **Public Methods**:
    - `def lookup_rule(category: str, rule_name: str) -> Dict[str, Any]`
    - `def check_token_compliance(token_type: str, value: Any) -> bool`
  - **Dependencies**: `vir_runtime.design.overrides`

### 3.2 DesignAuthorityAgent
- **Class / Module Name**: `vir_runtime.design.agent.DesignAuthorityAgent`
  - **Responsibilities**: Implement the Agent Contract interface, evaluate sensory evidence against design system guidelines.
  - **Constructor Parameters**:
    - `kb: DesignKnowledgeBase`
    - `bus: AsyncEventBus`
  - **Public Methods**:
    - `async def on_evidence_received(event: Event) -> None` - Handler triggered by Event Bus.
    - `async def issue_veto(reason: str, evidence: Evidence) -> None` - Publishes VETO event.

---

## 4. Detailed Interface Contracts

- **API Signature**: `def lookup_rule(category: str, rule_name: str) -> Dict[str, Any]`
  - **Parameters**:
    - `category` (string, e.g. `spacing`, `typography`, `color`)
    - `rule_name` (string mapping exact rule identifier inside config files)
  - **Return Types**: Returns a dictionary describing severity levels and limits.
  - **Exceptions**:
    - `RuleNotFoundError` - If category/name keys are missing from design system configurations.

---

## 5. Configuration Schema

- **Target Schema (`rules.yaml`)**:
```yaml
design_rules:
  color_palette:
    brand_primary: "#FF0000"
    severity: "MUST"
  spacing:
    grid_unit_px: 8
    severity: "SHOULD"
```

---

## 6. Database & Storage Design
- Design findings are saved to SQLite `vir_evidence` using classification `design`.

---

## 7. Cache Architecture
- **Design Tokens Cache**:
  - Memory dictionary caches rule lookup queries to prevent continuous disk reads.

---

## 8. Error Model

- **Exception Class**: `MUSTRuleViolation`
  - **Trigger Condition**: Design agent detects brand color usage violating configured MUST rules.
  - **Recovery Strategy**: Create `DesignFinding` record, issue a domain-specific VETO block event.
  - **Logging Requirements**: WARNING log referencing target DOM node bounding boxes.

---

## 9. Skill Integration Contracts
- **Skill Name**: `frontend-design`
  - **After Hooks**: Scans design findings outputs to suggest layout tweaks using correct design tokens.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Design Validation Flow**:
  1. `DesignAuthorityAgent` receives `evidence.new` event containing DOM computed colors.
  2. Query triggered: `kb.check_token_compliance("color", color_hex)`.
  3. Compliance returns `False`, checking rule severity level.
  4. Severity is `MUST`.
  5. `DesignAuthorityAgent` publishes `VETO` event with evidence uuid links.

---

## 12. Security & Safety
- **Pixel overrides containment**: Design override configurations prevent loading local files residing outside the project workspace folder boundaries.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_kb_queries.py` | `kb.py` | `self.assertEqual(rule["severity"], "MUST")` |
| `FR-13` | Unit Test | `tests/unit/test_design_vetos.py` | `veto.py` | `self.assertTrue(veto_emitted)` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Schema config -> `rules.yaml` -> `test_kb_queries.py` -> Verified.
- `FR-13` -> Task 1.9 -> Class `VetoHandler` -> `veto.py` -> `test_design_vetos.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/design/veto.py`
  - **Purpose**: Design rules severity enforcement processor.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on `design_finding.py`.
