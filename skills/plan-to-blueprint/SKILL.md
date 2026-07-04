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
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Generate a production-grade Technical Blueprint from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.
---

# Skill: Plan to Blueprint (FEAT-XXX format)

## Role

You are acting as a **Chief Software Architect**, **Senior Solution Architect**, and **Technical Reviewer**.

Your responsibility is to transform an approved implementation plan into a **production-grade Technical Blueprint** suitable for direct implementation by another AI or Senior Engineer.

---

# Objective

Upgrade the implementation plan into a production-grade Technical Blueprint. Do NOT merely transform the plan — act as an architect and reviewer to reduce uncertainty, analyze alternatives, evaluate risks, and enforce high architectural standards.

---

# Pre-flight & Global Policies

This Skill assumes `initialize-workflow` and `workflow-runtime` have completed.
Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification**.
Verify that the current checkpoint in `.session.json` is exactly `3` (Architecture Analysis Complete) – which is established upon completion of requirement discovery and planning.
1. If the session file is missing, if context health is `broken` (e.g. active branch or work item has drifted), or if the current checkpoint is not `3`:
   - Recommend running: `initialize-workflow`, `workflow-runtime` (to resume), or the preceding workflow skills to reach the correct checkpoint state.
   - Stop execution.
2. At the start of execution, update `.session.json` checkpoint to `4` (Blueprint/Fix Spec Generated) and set `"status"` to `"in_progress"`.
3. On successful generation of the blueprint file, update `.session.json` checkpoint to `4` (Blueprint/Fix Spec Generated), set `"status"` to `"completed"`, and output the runtime heartbeat before writing the file.
4. If execution fails or is aborted, set `"status"` to `"failed"`.

This Skill MUST strictly follow the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Before writing/overwriting files.
- **Memory First Policy** (Section 3) - When retrieving codebase context.
- **RAG Policy** (Section 4) - Using RAG search sequence.
- **Artifact Policy** (Section 5) - For generating blueprints under `docs/designs/` in `FEAT-XXX_slug_blueprint.md` format.

**Pre-flight Check**: Verify memory configuration `.agents/memory.config.json` and `<memory_root>/project-summary.md`. If memory confidence is low or absent, warn the user and stop.



## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)
---

# Input

```yaml
source_brainstorming: docs/brainstorm/FEAT-XXX_feature_slug.md
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
Read `docs/brainstorm/FEAT-XXX_feature_slug.md` and `docs/plans/FEAT-XXX_feature_slug_plan.md`. Extract **Feature ID**, **Feature Name**, requirements, scope, constraints, and recommendations from both documents.

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
Produce the blueprint. It must include the YAML metadata header and the design specifications:

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

# Technical Blueprint – [Human Readable Name]

## 0. Project Memory Baseline
- Memory state & Confidence
- RAG Queries and search results summarized
- Inspected source files (if any)

## 1. Component Architecture & Design
- **Affected Layers & Folders**: [Detailed directories and namespaces]
- **Public APIs / Interface Contracts**: [REST endpoints, RPC definitions, schemas]
- **Class / Interface Signatures**: [Exact types, fields, methods, parameters, and return types]
- **Data Models / Database Schema Definitions**: [SQL schemas, indexes, migrations, JSON layouts]
- **Folder / File Structure**: [NEW and MODIFY files mapped out]

## 2. Sequence & Interaction Diagrams
- [Mermaid sequence diagrams showing exact interaction loops between classes/services/APIs]

## 3. Data Flow / Sequence Flow
- [Detailed walkthrough of how data flows through components]

## 4. Alternative Solutions Considered & Trade-offs
- [Alternate designs, evaluated trade-offs, and reasons for rejection]

## 5. Architecture Decision Assessment
ADR Required: [Yes | No]

Reason:
[Justification for why an Architecture Decision Record is required or not. Examples: adding database dependencies, changing central authentication, introducing new frameworks.]

Recommended ADR Title:
[Proposed title, e.g., ADR-001 Cache Strategy for Playwright Assets]

Recommended Next Step:
- If ADR Required = Yes: run `/adr`
- If ADR Required = No: run `/implement`

## 6. Migration & Rollback Strategy
- [Database migration path, application backward compatibility, zero-downtime deployment plan]
- [Detailed rollback instructions and triggers]

## 7. Security & Permissions
- [Authentication protocols, authorization levels, input validation schemas, data encryption rules]

## 8. Performance & Scalability
- [Concurrency models, caching strategies, scaling considerations, latency impacts]

## 9. Error Handling & Resilience
- [Retry rules, fallback behaviors, timeout parameters, circuit breaker patterns]

## 10. Verification & Test Strategy
- [Unit test coverage specifications, mock boundaries, assertions, integration testing plan]
```

---

# Output Rules

Create exactly one file:
```
docs/designs/FEAT-XXX_feature_slug_blueprint.md
```

First line must be:
```html
<!-- File path: docs/designs/FEAT-XXX_feature_slug_blueprint.md -->
```

---

# Constraints

- Do NOT implement business logic.
- Do NOT skip sections.
- Keep naming consistent with project (from memory).
- **Do NOT create ADR files**. Only assess and recommend if they are required.

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
