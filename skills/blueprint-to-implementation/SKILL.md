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

This Skill assumes `initialize-workflow` and `workflow-runtime` have completed.
Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification**.
Verify that the current checkpoint in `.session.json` is exactly `4` (Blueprint/Fix Spec Generated) – which is established upon generation of the technical blueprint or fix spec.
1. If the session file is missing, if context health is `broken` (e.g. active branch or work item has drifted), or if the current checkpoint is not `4`:
   - Recommend running: `initialize-workflow`, `workflow-runtime` (to resume), or the preceding workflow skills to reach the correct checkpoint state.
   - Stop execution.
2. At the start of execution (during pre-flight checks), update `.session.json` checkpoint to `5` (Implementation Ready) and set `"status"` to `"in_progress"`.
3. Upon successful implementation of the feature and verification of tests, update `.session.json` checkpoint to `5` (Implementation Ready), set `"status"` to `"completed"`, and output the runtime heartbeat.
4. If implementation fails or is aborted, set `"status"` to `"failed"`.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code, creating, or overwriting files.
- **Git Workflow Policy** (Section 2) - Perform branch validation, status checks, and suggest feature branches (`feature/FEAT-XXX-slug`).
- **Memory First Policy** (Section 3) - When retrieving codebase context.
- **RAG Policy** (Section 4) - Using RAG search sequence.
- **Testing Policy** (Section 8) - Run build & compile verification; handle failure appropriately.



## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)
---

# Pre-flight: Memory Health Check & ADR Validation

**MANDATORY. Execute before writing any code.**
1. Verify memory configuration `.agents/memory.config.json` and `<memory_root>/project-summary.md`.
2. **ADR Validation Rule**:
   Read `docs/designs/FEAT-XXX_feature_slug_blueprint.md`. Find the `Architecture Decision Assessment` section.
   If the section states `ADR Required: Yes`:
   - Scan the `docs/adr/` folder.
   - Verify that a corresponding ADR document (e.g. `docs/adr/ADR-*.md`) referencing this Feature ID `FEAT-XXX` exists and has status `Accepted`.
   - **If the ADR file does NOT exist or is not Accepted**, STOP. Print:
     ```text
     ❌ ADR Verification Failed.
     
     This blueprint requires an approved Architecture Decision Record (ADR), but no matching accepted ADR was found in docs/adr/.
     
     Recommended Next Skill:
     create-adr
     
     Reason:
     You must document and accept the architectural decision using create-adr before implementation can proceed.
     
     Workflow Paused.
     ```
     Stop execution and wait for the user.

---

# Input

```yaml
phase: auto

design_file: docs/designs/FEAT-XXX_feature_slug_blueprint.md
# If auto, detect newest blueprint from docs/designs/

workspace: auto

language: auto

tech_stack: auto

architecture: auto

implementation_scope: auto

build_command: auto

test_command: auto
```

# Workflow

```
Step 1: Read Technical Blueprint & Perform ADR Validation
        ↓
Step 2: Pre-Implementation Git Gate
        - Run git branch & git status.
        - Ask choice (Continue on branch / Create new branch / Stop) and wait.
        ↓
Step 3: Consult Project Memory & RAG (No whole-workspace scanning)
        ↓
Step 4: Global Approval Gate
        - Explain modifications, list affected files and branch.
        - Ask "Proceed with implementation? [Y/N]" and STOP.
        ↓
Step 5: Code Implementation
        - Apply changes to source code.
        ↓
Step 6: Mandatory Validation Gate
        - Detect build/test/lint commands, run them, analyze and fix failures.
        ↓
Step 7: Generate Final Implementation Status Summary
```

# Mandatory Validation Gate

This gate runs after code generation and before the final summary. The Skill must never report success if validation fails.

This Skill MUST strictly execute the validation pipeline, detection rules, failure retries, and success criteria defined in **[AI_RULES.md](../../AI_RULES.md) (Section 11: Shared Validation Engine Policy)**.

---

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
