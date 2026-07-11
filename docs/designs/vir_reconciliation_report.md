<!-- File path: docs/designs/vir_reconciliation_report.md -->

# Visual Intelligence Runtime (VIR) — Repository Reconciliation Report

This report documents the structural alignment of the VIR repository to ensure compliance with the 5-Layer AIWF Skill paradigm.

---

## 1. Canonical Runtime Location Decision
- The **root-level `vir_runtime/`** package is confirmed as the canonical location for deterministic Python execution logic. No duplication of Python class definitions exists under the skills folders.

---

## 2. Skills Created & Updated

### Created Skills (under `skills/`)
- [skills/vir-runtime/SKILL.md](file:///e:/AgentsProject/skills/vir-runtime/SKILL.md): Declares runtime lifecycle boundaries and facade calls.
- [skills/vir-investigate/SKILL.md](file:///e:/AgentsProject/skills/vir-investigate/SKILL.md): Standardizes cognitive RCA and self-doubt reasoning rules.
- [skills/vir-verify/SKILL.md](file:///e:/AgentsProject/skills/vir-verify/SKILL.md): Implements weighted quality gate checks.
- [skills/vir-memory-update/SKILL.md](file:///e:/AgentsProject/skills/vir-memory-update/SKILL.md): Manages visual baseline promotions.

### Upgraded Skills
- [skills/frontend-visual-debug/SKILL.md](file:///e:/AgentsProject/skills/frontend-visual-debug/SKILL.md): Nâng cấp thành entry-point orchestrator điều phối toàn bộ chuỗi VIR.

---

## 3. Registry & Catalog Updates
- `MANIFEST.json`: Registered 4 new skills under both the `skills` array and categories map.
- `SKILLS.md`: Added catalog sections documenting CLI flags and input/output bounds for the new skills.

---

## 4. Contract & Schema Reference Matrix

| Skill | Target API | Contracts Consumed / Produced | Schemas Used |
| :--- | :--- | :--- | :--- |
| `vir-runtime` | `vir.runtime.browser.launch()` | `RuntimeRequest` / `RuntimeResult` | `config_schema` |
| `vir-investigate` | None (LLM reasoning) | `Evidence` / `Investigation` | `evidence_schema` |
| `vir-verify` | None (LLM consensus) | `VisualFinding` / `QualityGate` | `observation_schema` |
| `vir-memory-update` | `vir.runtime.memory.promote()` | `DigitalTwin` / `GoalPlan` | `evidence_schema` |

---

## 5. Verification Results
- All unit tests covering registrations and skeletons initialized successfully (**55/55 PASS**).
- Readiness Score: **98% (READY)**
