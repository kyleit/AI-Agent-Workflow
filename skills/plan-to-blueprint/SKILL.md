---
name: plan-to-blueprint
command: blueprint
aliases:
  - design
  - architecture
category: workflow
tags:
  - blueprint
  - design
  - architecture
version: 3.2.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-09
description: Generate a production-grade Technical Blueprint (Markdown & JSON) from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.
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
  usage: cached
---

# Skill: Plan to Blueprint (FEAT-XXX format)

## Role

You are acting as a **Chief Software Architect**, **Senior Solution Architect**, and **Technical Reviewer**.

Your responsibility is to transform an approved implementation plan into a **production-grade Technical Blueprint** suitable for direct implementation by another AI or Senior Engineer.

---

# Objective

Upgrade the implementation plan into a production-grade Technical Blueprint. Do NOT merely transform the plan — act as an architect and reviewer to reduce uncertainty, analyze alternatives, evaluate risks, and enforce high architectural standards.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "plan-to-blueprint" --command "blueprint" --checkpoint 4 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 4 --step "Step Complete" --next-skill "blueprint-to-implementation" --next-command "implement"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

# Input

```yaml
source_brainstorming: docs/brainstorming/FEAT-XXX_feature_slug.md
source_plan: docs/plans/FEAT-XXX_feature_slug_plan.md

workspace: auto

language: auto

tech_stack: auto

architecture: auto

output_path: docs/designs/auto
```

---

# Workflow

## Step 1 — Read Inputs
Read `docs/brainstorming/FEAT-XXX_feature_slug.md`. For the implementation plan, Architect MUST search for and read the structured JSON plan at `docs/plans/FEAT-XXX_feature_slug_plan.json` first. If it exists, read it to extract the phases, tasks, dependencies, parallel groups, exit criteria, rollback strategies, and tests with minimal token usage. If the JSON plan does not exist, fall back to reading `docs/plans/FEAT-XXX_feature_slug_plan.md`. Extract **Feature ID**, **Feature Name**, requirements, scope, constraints, and recommendations, as well as the **Traceability Matrix**, **Stakeholder Analysis**, **Data Flow**, **Open Decisions**, and **Risk Matrix** from both documents.

---

## Step 2 — Read Project Memory
Consult the memory summaries, interfaces, and architecture layers.

---

## Step 3 — RAG Query
Query `project-rag-search` for existing patterns and dependencies.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect source files directly only if memory gaps remain.

---

## Step 5 — Generate Technical Blueprint
Produce the blueprint. It must include the YAML metadata header and the design specifications. Architect MUST directly inherit and reuse the architecture principles, dependency graph, data flow, migration strategy, traceability matrix, open decisions, and risk matrix from the brainstorming spec, focusing strictly on detailed code mutations and interface contracts without repeating high-level analysis:

```markdown
<!-- File path: docs/designs/FEAT-XXX_feature_slug_blueprint.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: blueprint
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: ../plans/FEAT-XXX_feature_slug_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – [Human Readable Name]

## 0. Baseline Context & References
- **Memory Baseline**: [State and confidence levels retrieved from project memory summary]
- **RAG Query Summaries**: [List of vector search query results, matched files, and key findings]
- **Inspected Source Files**: [Target files inspected directly, including line references]

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `relative/path/to/file` | `[NEW | MODIFY | DELETE]` | [...] | [...] | [...] |

## 2. Target Folder Structure
```text
.
├── (exact directory structure)
```

## 3. Complete Class & Module Design
- **Class / Module Name**: `...`
  - **Responsibilities**: [...]
  - **Constructor Parameters**: [...]
  - **Public Methods**: `def method_name(...)` (Visibility: public)
  - **Internal Methods**: `def _internal_method(...)` (Visibility: internal)
  - **Dependencies**: [...]
  - **Extension Points**: [How subclasses can extend this]

## 4. Detailed Interface Contracts
- **API Signature**: `def api_name(param1: type) -> return_type`
  - **Parameters**: `param1` (validation rules, defaults)
  - **Return Types**: `return_type` description
  - **Exceptions**: `ExceptionName` thrown under Z conditions
  - **Validation Rules**: [...]
  - **Compatibility Notes**: [...]

## 5. Configuration Schema
- **Current Schema**: [...]
- **Target Schema**: [...]
- **Migration Rules**: [...]
- **Defaults & Validation**: [...]

## 6. Database & Storage Design
- **Tables**:
  - `table_name`: Columns, keys, nullability, constraints
- **Indexes**: Column mappings
- **Relationships / Constraints**: Foreign keys
- **Migration & Rollback Strategy**: SQL statements or scripts

## 7. Cache Architecture
- **Cache Keys**: Format and parameters
- **Invalidation Rules**: When cache is invalidated
- **TTL**: Time to live in seconds
- **Hash Strategy**: How keys are hashed
- **Provider versioning & stale detection**: [...]
- **Warmup & Cleanup**: [...]

## 8. Error Model
- **Exception Class**: `ExceptionName`
  - **Trigger Condition**: [...]
  - **Recovery Strategy**: [...]
  - **Retry Policy / Fallback**: Retry count, backoff, fallback behavior
  - **Logging Requirements**: Log level, context keys

## 9. Skill Integration Contracts
- **Skill Name**: `...`
  - **Before Hooks**: [...]
  - **After Hooks**: [...]
  - **Runtime Calls**: [...]
  - **Data Exchanged / Outputs**: [...]

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python workflow_runtime.py subcommand --arg`
  - **Parameters**: Option names, types, constraints
  - **Output**: JSON or text output schema
  - **Exit Codes**: 0 (success), 1 (general error)
  - **Failure behavior**: [...]

## 11. Sequence Flows
- **Normal Execution Flow**:
  1. Client calls API...
  2. ...
- **Cache Miss Flow**:
  1. Check cache (miss)...
  2. Query Provider...
- **Provider Unavailable Flow**:
  1. Provider throws exception...
  2. Fallback to default...

## 12. Security & Safety
- **Workspace Boundary**: Only write to relative workspace paths.
- **Path Validation**: Do not allow escape sequences like `../` to write outside sandbox.
- **Write Restrictions**: Specify forbidden directories.
- **Rollback safety**: [...]

## 13. Complete Test Matrix
| Requirement ID | Test Type (Unit/Integration/Compatibility/Regression/Performance/Stress/E2E) | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Unit Test | `relative/path/to/test_file.py` | `api.py` | `self.assertEqual(...)` |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `API` -> `api.py` -> `test_api.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `relative/path/to/file`
  - **Purpose**: [...]
  - **Owner**: [Architect / Coder / Reviewer / Verifier / Documentation / Runtime]
  - **Inputs / Outputs / Dependencies**: [...]
  - **Implementation Notes & Risks**: [...]
```

---

# Output Rules

Create exactly two files:
1. `docs/designs/FEAT-XXX_feature_slug_blueprint.md`
2. `docs/designs/FEAT-XXX_feature_slug_blueprint.json`

First line of the Markdown file must be:
```html
<!-- File path: docs/designs/FEAT-XXX_feature_slug_blueprint.md -->
```

The JSON file must conform to this schema:
```json
{
  "modules": [
    {
      "name": "...",
      "classes": [
        {
          "class_name": "...",
          "responsibilities": ["..."],
          "methods": [
            {
              "name": "...",
              "parameters": [],
              "return_type": "..."
            }
          ],
          "lifecycle": "...",
          "state_ownership": "..."
        }
      ]
    }
  ],
  "configuration": {
    "schema": {},
    "defaults": {}
  },
  "database": {
    "tables": [],
    "growth_estimation": "...",
    "maintenance_strategy": "..."
  },
  "cache": {
    "keys": [],
    "ttl_seconds": 600,
    "invalidation_rules": []
  },
  "errors": [
    {
      "exception_class": "...",
      "trigger": "...",
      "recovery": "..."
    }
  ],
  "sequence_flows": [
    {
      "flow_name": "...",
      "steps": []
    }
  ],
  "integration_contracts": [],
  "cli_contracts": [],
  "implementation_contracts": [
    {
      "file_path": "relative/path/to/file",
      "owner": "Coder",
      "notes": "..."
    }
  ],
  "implementation_packages": [
    {
      "task_id": "Task 1.1",
      "module": "...",
      "read_set": [],
      "write_set": [],
      "dependencies": [],
      "implementation_notes": "...",
      "verification": "...",
      "rollback": "...",
      "expected_outputs": []
    }
  ],
  "tests": [
    {
      "requirement_id": "REQ-001",
      "test_type": "Unit Test",
      "target_file": "relative/path/to/test_file.py"
    }
  ],
  "traceability": [],
  "artifacts": []
}
```

---

# Constraints

- Do NOT implement business logic.
- Do NOT skip sections.
- Keep naming consistent with project (from memory).
- **Do NOT create ADR files**. Only assess and recommend if they are required.
- **Mandatory Skill Skeleton**: If the blueprint introduces or creates a new skill directory under `skills/<skill-name>/`, it MUST also declare and generate a complete Skill skeleton in its proposed modifications. The skeleton MUST include: `skills/<skill-name>/SKILL.md` (containing Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations), `skills/<skill-name>/scripts/`, and `skills/<skill-name>/tests/` (if executable). If the blueprint creates a new skill path but does not define the SKILL.md file, validation must fail and the blueprint must not be marked complete.
- **Run a self-review of the generated blueprint against the "Disallowed Outputs Validation" checklist and fix all violations before saving.**

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert an approved Implementation Plan into a detailed Technical Blueprint. Once `docs/designs/FEAT-XXX_feature_slug_blueprint.md` is generated, STOP.

## 2. Never Execute Next Phase
Do NOT invoke `blueprint-to-implementation` or `create-adr`. Only recommend.

## 3. Workspace Modification Policy
Only create or update the target Technical Blueprint file.

---

## Completion Contract

```text
Current Phase:
Phase 3 — Plan to Blueprint

Status:
Completed

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Queries:
[list of queries and key findings]

Source Files Inspected:
[list or "None — all context from memory"]

Generated Output:
docs/designs/FEAT-XXX_feature_slug_blueprint.md

Recommended Next Skill:
[create-adr (if ADR Required = Yes) | blueprint-to-implementation (if ADR Required = No)]

Workflow Paused.
```
