---
name: implementation-to-release
command: release
aliases:
  - publish
  - ship
category: workflow
tags:
  - release
  - versioning
  - publish
version: 3.0.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-06
description: Enforces explicit user-driven releases and requires blueprint validation before any release activities.
---

# Skill: Implementation to Release (Explicit & Blueprint-Validated)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 9"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "implementation-to-release" --command "release" --checkpoint 10 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 10 --step "Step Complete" --next-skill "project-memory-update" --next-command "memory-sync"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Explicit Release Policy** (Section 9) - Never release automatically.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.

---

## 🔒 EXPLICIT RELEASE GATES

Prior to running any release activities, the AI must strictly execute the following validations:

1. **Verify Explicit Release Request**: The AI must verify that the user has explicitly requested a Release (e.g. via keywords like `/release`, `release`, `create release`, `publish release`, `bump version`, `commit and push`, or `tag this version`). Any automatic progression to this Skill without a clear user request is strictly prohibited.
2. **Verify Blueprint Approval**: Confirm that a Technical Design Blueprint exists for this work under `docs/designs/` and that its status is marked as `"approved": true` in the active workflow session data.
3. **Verify Quality Gates**: Ensure all quality gates are met:
   - Debug Gate: `docs/debug/FEAT-XXX_debug.md` has `status: PASS`.
   - Verification Gate: `docs/verification/FEAT-XXX_verify.md` has `status: PASS`.

**If any validation fails:**
- **STOP immediately**.
- Print the warning: `❌ Release aborted: No explicit release request or approved Blueprint found. The framework forbids automatic releases. Please run /release only when you are ready to publish.`
- Do NOT perform version bumps, modify changelogs, commit, tag, push, or merge.

## Interactive Choice Protocol for Release Gates

Every approval gate in **Phase 8 (Release Summary)**, **Phase 9 (Commit Release)**, and **Phase 11 (Push Branch)** MUST be performed using the Centralized CLI Choice Protocol:
1. Run:
   ```bash
   python skills/workflow-runtime/scripts/workflow_runtime.py choice create --id "release_approval" --title "Release/Commit/Push Approval" --desc "Verify and approve the release step to proceed." --type approval
   ```
2. Run:
   ```bash
   python skills/workflow-runtime/scripts/workflow_runtime.py choice wait --id "release_approval"
   ```
3. Read result:
   ```bash
   python skills/workflow-runtime/scripts/workflow_runtime.py choice read --id "release_approval"
   ```
If the result is `approve`, proceed to the next step. If `cancel`, stop.

---

## Workflow Sequence

The release process runs in 11 sequential phases:

```
Phase 1: Read release.config.json
         ↓
Phase 2: Detect changed files via 'git diff' to identify affected modules
         ↓
Phase 3: Display affected modules list
         ↓
Phase 4: Determine current version and target new version (Major/Minor/Patch)
         ↓
Phase 5: Update version files ONLY for affected modules (never modify unrelated ones)
         ↓
Phase 6: Update Module CHANGELOG.md files for every affected module
         ↓
Phase 7: Compile Root CHANGELOG.md detailing version changes and highlights
         ↓
Phase 8: Approval Gate - Present Release Summary and query user using:
         ```bash
         python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose release action:" --options "Continue|Cancel" --default "Cancel"
         ```
         ↓
Phase 9: Commit release updates (Requires explicit approval)
         ↓
Phase 10: Compile and write Git tags (single or module-specific; no duplicates)
         ↓
Phase 11: Push branch and tags (Requires explicit approval)
```

---

## Completion Contract

Upon completion, output this plain text report:

```text
Current Phase:
Phase 5 — Implementation to Release

Status:
Completed

Release Summary:
- Release Mode:    [single | module]
- Branch Status:   [main | master | merged]
- Affected Modules:[list of affected modules]
- Git Tag(s) Written: [vX.Y.Z | module/vX.Y.Z | none]

Recommended Next Skill:
project-memory-update

Workflow Paused.
```
