---
name: workflow-runtime
command: runtime
aliases:
  - engine
category: runtime
tags:
  - runtime
  - controller
  - session
version: 2.12.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-06
description: Runtime controller for the AI Engineering Workflow. Manages execution session state (.session.json), validates context health, detects context drift, updates checkpoints, supports recovery via resume-workflow, and outputs runtime heartbeats. Read-only.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: none
  rag: none
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
---

# Skill: workflow-runtime (AI Workflow Runtime Controller)

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

## Purpose
The **workflow-runtime** Skill acts as the centralized execution state controller for all AI skills. It encapsulates atomic session updates, Git check-pointing, token usage estimations, context drift checks, and workspace validations.

---

## Runtime CLI Commands
The runtime CLI engine is written in Python and entrypoint is:
`aiwf <subcommand>`

Agents SHOULD invoke the project CLI wrapper (`aiwf ...`) or direct module invocation `aiwf <subcommand>`. Direct Python invocation is a maintainer/debug fallback only, because some IDEs require approval for every Python command.

## Unified CLI Reference

> **⚠️ IMPORTANT FOR AI AGENTS**: 
> The `aiwf` CLI now contains over 62 commands across 16 categories. The full documentation and syntax guide has been extracted to a dedicated reference file.
> 
> **You MUST read the following file before executing any `aiwf` command:**
> 👉 [references/CLI_REFERENCE.md](references/CLI_REFERENCE.md)

### Quick Invocation Example
- Execute coordinator tick:
  `aiwf coordinator --tick [--dry-run]`
- Read execution state:
  `aiwf state --action read [--file .agents/state/workflow.json]`

---

## Troubleshooting & Failure Recovery
- **Corrupted Session File**: If `.session.json` becomes corrupted, the model will output an empty state check error. Run `init` to automatically regenerate a healthy schema without changing the conversation ID.
- **Git Branch Mismatch**: If you switch git branches during execution, `validate` or `heartbeat` will warn or return code 1 due to `context_health` drift detection. Ensure you are on the approved feature branch before running any modifications.
