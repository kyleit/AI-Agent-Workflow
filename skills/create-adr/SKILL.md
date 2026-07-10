---
name: create-adr
command: adr
aliases:
  - architecture-decision
category: architecture
tags:
  - adr
  - architecture
  - decision
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Create Architecture Decision Records (ADRs) only when explicitly invoked.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: none
---

# Skill: Create Architecture Decision Record (ADR)

## Purpose

This Skill is used to record and document critical architectural decisions and their trade-offs. It is invoked when `plan-to-blueprint` recommends an ADR, or when a developer determines a significant architecture decision is required.

It creates a dedicated ADR document under:
```text
docs/adr/ADR-XXX_short_title.md
```

This Skill does NOT generate source code, plans, or implementation designs.

---

## Role

You are acting as a **Principal Software Architect** and **Technical Authority**.

---

## Input

```yaml
title: "Decide on cache strategy for Playwright assets"
# Short title of the architecture decision (required)

related_feature: "docs/brainstorm/FEAT-XXX_feature_slug.md"
# Relative path to the related brainstorming or requirement discovery document

design_file: "docs/designs/FEAT-XXX_feature_slug_blueprint.md"
# Relative path to the blueprint design (optional)
```

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "at least 1"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "create-adr" --command "adr" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ADR Numbering Rules

This Skill MUST follow the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before writing the ADR file.
- **Artifact Policy** (Section 5) - For generating ADRs under `docs/adr/` in `ADR-XXX_slug.md` format.

Calculate the next ADR ID by scanning `docs/adr/` as defined in Section 5 (Artifact Policy) of `AI_RULES.md`. If empty, start at `ADR-001`. Otherwise, use `highest_id + 1`.

---

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

## Output Rules

Create exactly one file under `docs/adr/`:
```text
docs/adr/ADR-XXX_short_title.md
```
*(Replace `XXX` with the calculated ADR ID, and `short_title` with a clean, lowercase, underscore-separated slug, e.g., `docs/adr/ADR-001_cache_strategy.md`)*

The generated file must contain:

```markdown
<!-- File path: docs/adr/ADR-XXX_short_title.md -->

# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Rejected | Superseded]

## Related Feature
[FEAT-XXX (e.g. FEAT-001)]

## Context
[What is the context, problem description, and drivers of this decision?]

## Decision
[What is the selected option/architecture decision?]

## Alternatives Considered
[What alternative options were evaluated and rejected?]

## Trade-offs
[What are the pros and cons of the options considered?]

## Consequences
[What is the consequence of this decision on the codebase and future work?]

## Risks
[What risks does this decision introduce and how will they be mitigated?]

## References
[Links to related features, plans, designs, or external documentations]
```

---

## Capability Boundary & Guardrails

- **Allowed Output**: The Skill only owns and is allowed to write files under `docs/adr/` in the format `ADR-XXX_slug.md`.
- **No Code Modification**: The Skill must NEVER modify source code, configurations, tests, build scripts, or documentations outside `docs/adr/` as defined in [AI_RULES.md](../../AI_RULES.md).
- **No Downstream Tasks**: The Skill must NEVER generate plans, blueprints, or source code.
- **Independent Invocation**: Do NOT execute other skills automatically. Refer to [AI_RULES.md](../../AI_RULES.md) for pure workflow limits.

---

## Completion Contract

```text
Current Phase:
Architecture Decision Record (ADR) Creation

Status:
Completed

ADR Generated:
docs/adr/ADR-XXX_short_title.md

ADR ID:
ADR-XXX

Related Feature ID:
FEAT-XXX

Workflow Paused.
```
