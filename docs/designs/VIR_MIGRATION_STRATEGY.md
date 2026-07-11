<!-- File path: docs/designs/VIR_MIGRATION_STRATEGY.md -->

# Visual Intelligence Runtime (VIR) — Layered Migration Strategy

This document details the migration path to transition VIR from its initial script-centric layout to the refactored **5-Layer Skills + Runtime Architecture**.

---

## 1. Directory Structure Target Blueprint

We transition the workspace folders to distinct boundaries matching the layers:

```text
e:/AgentsProject/
├── .agents/
│   └── skills/                         <-- Layer 1: Skills specifications
│       ├── vir-runtime/
│       │   └── SKILL.md
│       ├── vir-verify/
│       │   └── SKILL.md
│       └── vir-memory-update/
│           └── SKILL.md
├── docs/
│   └── designs/
│       ├── contracts/                  <-- Layer 3: Public API Contracts (.json)
│       │   ├── runtime_api_v1.json
│       │   └── evidence_contract_v1.json
│       └── schemas/                    <-- Layer 4: Machine-readable Schemas (.json)
│           ├── evidence_schema.json
│           ├── observation_schema.json
│           └── config_schema.json
└── vir_runtime/                        <-- Layer 2 & 5: Runtime & Python Implementation
    ├── core/                           
    │   ├── api.py                      <-- Layer 2: Stable exposed Runtime API facade
    │   ├── bus.py                      <-- Layer 5: Event loop protector execution engine
    │   └── runtime.py
    ├── sensory/                        <-- Layer 5: Deterministic inputs engines
    │   ├── vision/
    │   └── touch.py
    └── sandbox/                        <-- Layer 5: Sandbox process trackers
```

---

## 2. Boundary Definitions

### Skill Boundaries (Layer 1)
- Skills contain **no deterministic Python code** nor business logic.
- They are written entirely in declarative `SKILL.md` documents.
- They define guidelines, context mapping rules, allowed/forbidden commands, and prompt structures.

### Runtime API Boundaries (Layer 2)
- The runtime exposes a single stable facade interface `vir_runtime/core/api.py`.
- No LLM/VLM calls are made here. The API accepts structural calls (e.g. `capture_screenshot()`, `inject_a11y_axe()`).

### Contracts & Schemas Boundaries (Layers 3 & 4)
- Skills and Runtimes do **not** import internal classes.
- They communicate exclusively by serialization matching target contracts (e.g., standard `Evidence` JSON envelope).

### Python Implementation Boundaries (Layer 5)
- Executes purely deterministic low-level commands.
- Never decides design conformity; only provides pixel mismatch indexes, console log files, or accessibility arrays.

---

## 3. Migration Tasks & Target Relocations

| Current File | Target Module / Layer | Migration Action |
| :--- | :--- | :--- |
| `vir_runtime/cognitive/pipeline.py` | Relocated to `.agents/skills/vir-runtime/SKILL.md` | Remove Python orchestration loop; write declarative 11-stage prompts in Skill |
| `vir_runtime/design/agent.py` | Relocated to `.agents/skills/vir-verify/SKILL.md` | Rewrite style evaluation checks as VLM audit rules within verification skill |
| `vir_runtime/memory/learning.py` | Relocated to `.agents/skills/vir-memory-update/SKILL.md` | Relocate lessons extraction to VLM synthesis skill instructions |
| `vir_runtime/sensory/vision/pixel_comparer.py` | `vir_runtime/sensory/vision/` (Layer 5) | Keep as deterministic pixel diff utility in implementation |
| `vir_runtime/sandbox/process.py` | `vir_runtime/sandbox/` (Layer 5) | Keep as standard Win32 subprocess killer in implementation |
