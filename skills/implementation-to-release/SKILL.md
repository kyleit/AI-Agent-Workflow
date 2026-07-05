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
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Perform configuration-driven, module-aware release activities including version updates, changelogs, branch merges, git commits, tags, and pushes based on release.config.json.
---

# Skill: Implementation to Release (Configuration-Driven & Module-Aware)

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill assumes `initialize-workflow` and `workflow-runtime` have completed.
Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification**.
Verify that the current checkpoint in `.session.json` is exactly `9` (Verification Complete).
1. If the session file is missing, if context health is `broken` (e.g. active branch or work item has drifted), or if the current checkpoint is not `9`:
   - Recommend running: `debug-to-verify` (command: `/verify`) to reach the correct checkpoint state.
   - Stop execution.
2. At the start of execution, set `"status"` to `"in_progress"`.
3. Upon successful release tag/push, update `.session.json` checkpoint to `10` (Release Complete), set `"status"` to `"completed"`, and output the runtime heartbeat.
4. If execution fails, set `"status"` to `"failed"`.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly follow the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before writing version files, commits, tags, or pushing.
- **Git Workflow Policy** (Section 2) - Perform branch verification, tag compilation, and remote pushes.
- **Artifact Policy** (Section 5) - Do NOT create folders under `docs/releases/`.
- **Versioning Policy** (Section 6) - Follow Semantic Versioning rules.
- **Testing Policy** (Section 8) - Compile and run verification commands prior to releasing.
- **Release Policy** (Section 9) - Follow configuration-driven multi-module sequences.

---

## Multi-Agent Contract

This Skill runs under the Multi-Agent Workflow.
It must respect agent ownership and handoff rules defined in:
- [agents/](../../agents/)
- [runtime/](../../runtime/)

---

## 🔒 RELEASE CONFIGURATION & AUTO-DETECTION

At startup, read `.agents/release.config.json`.
- **If the configuration file is missing**:
  - Scan the workspace to automatically detect project types (Go, Node, Python, Rust, Java, etc.).
  - Determine version file paths, changelogs, and module roots.
  - Present the detected layout and ask for user approval **before** generating `.agents/release.config.json`. Never create the file automatically.

---

## 🔒 QUALITY GATE VERIFICATION ENFORCEMENT

Prior to beginning the release sequence, verify that all three quality gates are met:
1.  **Debug Gate**:
    - Locate `docs/debug/FEAT-XXX_debug.md` (or equivalent issue fix file).
    - Must have `status: PASS`.
2.  **Visual Debug Gate** (If UI/Frontend feature):
    - Locate `docs/verification/FEAT-XXX_visual_debug.md` (or equivalent issue visual debug file).
    - Must have `status: PASS` or `status: PARTIAL` (if browser tools were unavailable).
    - Skip check only if backend-only feature (marked as skipped in session or no UI files affected).
3.  **Verification Gate**:
    - Locate `docs/verification/FEAT-XXX_verify.md` (or equivalent verification file).
    - Must have `status: PASS`.

**Strict Policy**:
- If all applicable gates are passed (`PASS`/`PARTIAL`), proceed with Phase 1.
- If any quality gate fails (or the report file is missing):
  - **STOP execution immediately**.
  - Display a block describing the quality failure: `❌ Release is forbidden because the feature has not passed all required quality gates (Debug: PASS, Visual Debug: PASS/PARTIAL/Skipped, Verify: PASS).`
  - Instruct the agent/user to return to the appropriate quality stage (`/debug` or `/visual-debug` or `/verify`) to resolve the issues.
  - Set `.session.json` status to `"failed"`.

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
Phase 8: Approval Gate - Present Release Summary and await Y/N confirmation
         ↓
Phase 9: Commit release updates (Requires explicit approval)
         ↓
Phase 10: Compile and write Git tags (single or module-specific; no duplicates)
         ↓
Phase 11: Push branch and tags (Requires explicit approval)
```

---

## Shared Module Dependency Detection

If any changed files belong to a shared component directory (such as `shared/`, `common/`, `libs/`, `packages/`):
1. Identify all dependent modules within the project configuration.
2. Prompt the user to choose whether these dependent modules should also receive version bumps.
3. Never assume or auto-bump without explicit confirmation.

---

## Git Safety & Branch Handling

- **Branch Check**: Prior to releasing, check the current branch. If it is NOT `main` or `master`, prompt the user: `Merge to main? [Y/N]`. Never merge automatically.
- **Safety Guards**: Never force push (`-f`), force tag, force merge, rebase automatically, or delete active branches or tags.
- **Non-Git Projects**: If Git is unavailable:
  - Skip checkout, merge, commit, tag, and push phases.
  - Still update version files, write local/root changelogs, and print the Release Summary.

---

## Post-Release Memory & Runtime Sync

After a successful release:
1. **Memory Update**: Update Project Memory, Lessons Learned, Release History, and Version History records.
2. **Runtime Update**: Update Workflow Runtime context state (`.session.json`) with `current_version`, `latest_release`, `git_tag`, and `current_branch`.

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
