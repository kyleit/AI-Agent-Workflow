---
name: blueprint-to-implementation
command: implement
aliases:
  - code
  - build
category: workflow
tags:
  - implementation
  - code
  - generation
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Implement production-ready source code from an approved Technical Blueprint using a Memory-First strategy, the FEAT-XXX Feature ID format, and Git pre-implementation approval gates.
---

# Skill: Blueprint to Implementation (FEAT-XXX format)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 4"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "blueprint-to-implementation" --command "implement" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "implementation-to-debug" --next-command "debug"` when execution finishes successfully.
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

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 4"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "blueprint-to-implementation" --command "implement" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "implementation-to-debug" --next-command "debug"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## Final Summary Format

Upon completion of the implementation and validation phase, print this exact final summary format to the console and update `.session.json`:

```markdown
## Implementation Status

[PASS | FAILED]

## Implemented

- [Bullet points of implemented features/modules]

## Files Created

- [List of created files or "None"]

## Files Modified

- [List of modified files or "None"]

## Validation

### Build

Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Tests

Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Lint

Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Typecheck

Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Self Review

Result: [PASS | FAILED]

## Issues Fixed During Validation

- [Bullet points of fixes applied during validation or "None"]

## Remaining Issues

- [Bullet points of remaining/unresolved issues or "None"]

## Recommended Next Skill

- If PASS: /debug or /verify
- If FAILED: /debug

Workflow Paused.
```
