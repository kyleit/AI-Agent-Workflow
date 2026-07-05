---
name: brainstorming-to-plan
command: plan
aliases:
  - planning
  - planning-phase
category: workflow
tags:
  - planning
  - workflow
  - scoping
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

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3 or 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "brainstorming-to-plan" --command "plan" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"` when execution finishes successfully.
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
