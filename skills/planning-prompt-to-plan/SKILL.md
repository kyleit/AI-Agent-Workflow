---
name: planning-prompt-to-plan
command: plan-legacy
aliases:
  - planning-legacy
category: workflow
tags:
  - legacy
  - planning
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Convert a structured master brainstorming document into a formal Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.
---

# Skill: Planning Prompt → Implementation Plan (FEAT-XXX format)

## Purpose

Execute a planning prompt from a master brainstorming document and generate a complete, production-ready Implementation Plan under `docs/plans/`.

This Skill must NOT generate:
- Technical Blueprint (Design)
- Architecture Decision Records (ADRs)
- Source code
- Tests

Its only responsibility is creating the implementation planning document.

---

## Role

You are acting as a **Senior Software Architect**, **Technical Planner**, and **System Analyst**.

Your responsibility is to produce a production-ready Implementation Plan with the **lowest possible token usage** by reading memory before reading source code.

---

## Input

```yaml
prompt_file: docs/brainstorm/FEAT-XXX_feature_slug.md
# Path to the brainstorming/requirement discovery file containing the planning prompt

workspace: auto

language: auto

framework: auto

architecture: auto

output_path: docs/plans/auto
```

---

# Pre-flight: Memory Health Check

**MANDATORY. Execute before any analysis.**
Verify that memory configuration `.agents/memory.config.json` and `<memory_root>/project-summary.md` are present. If memory confidence is low or absent, warn the user and stop.

---

# Workspace Reading Policy

**MANDATORY. Never scan the entire workspace.**
Read in this strict order. Stop at each level once sufficient context is found:
1. `<memory_root>/project-summary.md`
2. `<memory_root>/architecture/` layout files
3. `<memory_root>/modules/` / `<memory_root>/services/` files
4. `<memory_root>/lessons/`
5. `project-rag-search` tool query
6. Targeted source inspection (ONLY if gaps remain)

---

# Workflow

## Step 1 — Read Master Requirement Document
Read the brainstorming file at:
```
docs/brainstorm/FEAT-XXX_feature_slug.md
```
Extract the **Feature ID**, **Feature Name**, and the **Planning Prompt** section from it.

---

## Step 2 — Read Project Memory
Consult the memory summary and files to check the target codebase design and conventions.

---

## Step 3 — RAG Query
Query `project-rag-search` with the feature name and related keywords.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect only files explicitly referenced by memory or RAG.

---

## Step 5 — Generate Implementation Plan
Generate the plan document. It must contain the YAML metadata header and the plan sections:

```markdown
<!-- File path: docs/plans/FEAT-XXX_feature_slug_plan.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: planning
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: ../brainstorm/FEAT-XXX_feature_slug.md
next_artifact: ../designs/FEAT-XXX_feature_slug_blueprint.md
---

# FEAT-XXX: [Human Readable Name]

## Objective
- [Business objective / Why is this feature needed?]
- [Expected outcome / Success definition]

## Scope
### Included
- [What is in scope]

### Excluded
- [What is explicitly excluded]

## Project Impact
- [High-level impacted areas: Modules, Services, APIs, Database, Cache, Config, UI, Background Jobs]

## Dependencies
- [External systems, existing project components, prerequisites]

## Risks
- [Risk description, impact, suggested mitigation]

## Acceptance Criteria
- [Measurable/verifiable completion criteria]

## Deliverables
- [High-level list of deliverables]

## Estimated Complexity
- [Low / Medium / High + explanation]

## Recommended Blueprint Focus
- [Guidance for the subsequent Technical Design Blueprint phase: e.g., cache invalidation strategy, background sync. Guidance only, no technical design]

## Recommended Next Skill
/blueprint
```

---

# Output Rules

Create exactly one file:
```
docs/plans/FEAT-XXX_feature_slug_plan.md
```

First line must be:
```html
<!-- File path: docs/plans/FEAT-XXX_feature_slug_plan.md -->
```

---

# Constraints

- Do NOT describe technical implementation.
- Do NOT define classes, functions, or interfaces.
- Do NOT define APIs, database schemas, SQL, or folder structures.
- Do NOT generate pseudo-code.
- Planning must remain understandable by both technical and non-technical stakeholders.
- Keep the plan concise and focused entirely on project management.

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert a master brainstorming planning prompt into a formal Implementation Plan. Once `docs/plans/FEAT-XXX_feature_slug_plan.md` is generated, STOP.

## 2. Never Execute Next Phase
Do NOT invoke `plan-to-blueprint` or any other Skill.

## 3. Workspace Modification Policy
Only create or update the target implementation plan file. No source code changes.

---

## Completion Contract

```text
Current Phase:
Phase 2 — Planning Prompt to Plan

Status:
Completed

Memory Status:
[Fresh | Medium | Low]

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Query:
[query text used]

Source Files Inspected:
[list or "None — answered from memory"]

Generated Output:
docs/plans/FEAT-XXX_feature_slug_plan.md

Recommended Next Skill:
plan-to-blueprint

Workflow Paused.
```
