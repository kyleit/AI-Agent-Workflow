---
name: skill-self-verification
description: Automatically check and verify other Skills within the AI Skill Framework using Behavioral Acceptance Testing (BAT).
command: /verify-skill
aliases:
  - verify-skill
  - skill-verify
  - self-verify
category: quality
tags:
  - verification
  - testing
  - skills
  - runtime
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: none
  rag: none
  workspace_scan: none
  environment: cached
  version: none
  provider: optional
  usage: none
---

# Skill: skill-self-verification (Behavioral Acceptance Testing)

## Overview
This Skill acts as a simulated end user executing **Behavioral Acceptance Testing (BAT)** to evaluate interaction flows, user experience (UX), token consumption, and business value of any newly created or modified Skill before release.

## Purpose
The objective is to automate behavioral validation to ensure:
- Realistic user personas are simulated to interact with the target Skill.
- End-to-end conversations, prompts, and approval gates are tested and resolved (accept/reject).
- Quantitative UX review, workflow quality, and productivity gains are measured.
- Detailed Before vs After code diff comparison is provided for modified Skills.
- A comprehensive BAT verification report is generated to guarantee intended business value.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill interfaces with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "optional"` before taking any action.
- **Progress Tracking**: Update status and log progress using `workflow_runtime.py` when integrated in a workflow session.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill strictly adheres to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.

## 2. Input Schema
- `skill` (string, required): Folder name of the target Skill to verify (e.g., `orchestrator`, `quick-fix`).

## 3. Workflow (BAT Pipeline)
1. **Goal Extraction**: Read the target Skill's description and design goals.
2. **Persona Generation**: Create realistic personas mapping to the target Skill's domains.
3. **Simulation Phase**: Execute simulated end-to-end sessions, resolving all choice prompts and gates.
4. **Before vs After comparison**: Run automated git diff analysis to capture change summaries.
5. **Metrics Evaluation**: Measure UX rating, productivity gains, and Gemini API token costs.
6. **Report Generation Phase**: Write the markdown BAT report at `docs/verification/SKILL-VERIFY_<skill-name>.md`.

## 4. Run Commands
```bash
python skills/skill-self-verification/scripts/verify_skill.py verify --skill <skill-name>
```

## 5. Completion Criteria
- Verification report generated with all 12 mandatory BAT sections.
- Achieves a final `PASS` status approved by the simulated user agent.
