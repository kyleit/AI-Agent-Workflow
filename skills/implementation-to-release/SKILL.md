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
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-06
description: Enforces explicit user-driven releases with workflow-aware validation before any release activities.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: none
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
---

# Skill: Implementation to Release (Explicit & Workflow-Aware)

## Purpose

Enforces explicit user-driven releases with validation matched to the release context.

---

## ðŸ”’ WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the AIWF Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint (Workflow Release Mode only)**: If `.agents/state/workflow.json` has an active workflow or active work item, validate that the workflow has reached the post-verification release point before taking release action. Prefer `aiwf` runtime commands when available. If validation fails in Workflow Release Mode, halt execution immediately.
- **Maintenance Release Mode**: If no active workflow exists and the current user turn explicitly requests release, do not require checkpoint 9 and do not abort only because `.agents/state/workflow.json` has `active_workflow: null`. Continue with explicit release request validation, reviewed Git diff, targeted tests, version/changelog update, public export, and release approval.
- **Progress Tracking**:
  - *Start*: Use `aiwf start --skill "implementation-to-release" --command "release" --checkpoint 10 --step "Starting execution..."` when the runtime CLI is available.
  - *Step Updates*: Use `aiwf step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Use `aiwf complete --checkpoint 10 --step "Step Complete" --next-skill "project-memory-update" --next-command "memory-sync"` when execution finishes successfully.
  - *Failure*: Use `aiwf fail --step "<error_step>" --log "<error_details>"` if any phase fails.
  - If the runtime CLI is unavailable or the IDE blocks runtime commands, continue the release workflow using file/state evidence and report the runtime bridge limitation explicitly.

---

## ðŸ”’ GLOBAL POLICY REFERENCES

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

## ðŸ”’ RUNTIME DAEMON COMMAND BUS EXECUTOR

When the shared Runtime Daemon is active, agents MUST execute build, export, commit, publish, and update operations by writing `.agents/runtime/commands/runtime.request.json` command requests rather than running raw interactive shell commands that trigger IDE approval popups.

**NON-BLOCKING SCHEDULE WAITING PROTOCOL**:
- **Step 1**: Write `.agents/runtime/commands/runtime.request.json` with the requested command.
- **Step 2**: **DO NOT** run `workflow_runtime runtime process` or shell commands to trigger processing. The background daemon will process it automatically.
- **Step 3**: Immediately call the `schedule` tool with a 3-second timer (`DurationSeconds="3"`, `Prompt="Check .agents/runtime/commands/runtime.response.json for command bus completion result."`).
- **Step 4**: When woken by the timer, read `.agents/runtime/commands/runtime.response.json` using `view_file` to verify `status: "OK"`.

Supported daemon commands for release:
- `export.build`: Runs `make export` ngầm.
- `git.add`: Runs `git add <files>` ngầm.
- `git.commit`: Runs `git commit -m "<message>"` ngầm.
- `release.publish`: Runs `make publish-github` ngầm.
- `framework.update`: Runs `aiwf update` ngầm.

Example request format for `release.publish`:
```json
{
  "type": "RUNTIME_COMMAND",
  "command": "release.publish",
  "args": {},
  "idempotency_key": "release-publish-v6-20-12",
  "requested_at": "2026-07-26T23:56:00Z"
}
```

Example request format for `git.commit`:
```json
{
  "type": "RUNTIME_COMMAND",
  "command": "git.commit",
  "args": {
    "message": "chore(release): bump version to 6.20.12"
  },
  "idempotency_key": "git-commit-v6-20-12",
  "requested_at": "2026-07-26T23:56:00Z"
}
```

> **CRITICAL RULE**: The runtime daemon is a "dumb" executor. It DOES NOT auto-generate commit messages, changelogs, or determine version bumps. You (the Agent) MUST write the `CHANGELOG.md` and update `MANIFEST.json` yourself using IDE file-editing tools. When triggering `git.commit`, you MUST explicitly provide the commit message inside the `"args": {"message": "..."}` payload.

---

## ðŸ”’ EXPLICIT RELEASE GATES

Prior to running any release activities, the AI must strictly execute the following validations:

1. **Verify Explicit Release Request**: The AI must verify that the user has explicitly requested a Release (e.g. via keywords like `/release`, `release`, `create release`, `publish release`, `bump version`, `commit and push`, or `tag this version`). Any automatic progression to this Skill without a clear user request is strictly prohibited.
2. **Determine Release Context**:
   - **Workflow Release Mode**: If `.agents/state/workflow.json` has an active workflow or active work item, release is tied to that workflow.
   - **Explicit Maintenance Release Mode**: If no active workflow exists, release may proceed only when the current user message explicitly requests release. This mode is intended for already-implemented maintenance changes, documentation/rule updates, packaging updates, source-export updates, or hotfixes that were completed outside an active workflow session. Absence of an active workflow is not, by itself, a release blocker in this mode.
3. **Workflow Release Mode Gates**: When an active workflow exists, confirm that:
   - A Technical Design Blueprint exists for this work under `docs/features/<feature-family>/blueprints/`.
   - The active workflow session data marks the exact Blueprint as `"approved": true`.
   - Debug Gate: `docs/features/<feature-family>/debug/<WORK_ITEM_ID>_<slug>_debug.md` has `status: PASS`.
   - Verification Gate: `docs/features/<feature-family>/verification/<WORK_ITEM_ID>_<slug>_verify.md` has `status: PASS`.
4. **Explicit Maintenance Release Mode Gates**: When no active workflow exists, do not require a Blueprint. Instead, the Release Manager MUST:
   - Confirm the user explicitly requested release in the current conversation turn.
   - Inspect the current Git diff and list the files that will be included.
   - Exclude unrelated dirty files from staging.
   - Run targeted tests or validation for the changed files. Do not run the full test suite unless the user requested it or the release affects broad shared behavior.
   - Update version and root `CHANGELOG.md`.
   - Run `make export` and stage `public_export` if this repository uses public export.
   - Check `.agents/memory/`; if memory files changed, stage them before commit.
   - Verify that `CHANGELOG.md` does not contain local absolute paths or `file://` links.
5. **Walkthrough Handover Decision Gate**: The AI must prompt the user using the Choice Protocol before packaging or overwriting `walkthrough.md` in the repository, asking whether they want to overwrite (create new walkthrough) or keep/append to the previous history.

**If any validation fails:**
- **STOP immediately**.
- Print the specific failed gate and the exact evidence that is missing.
- For Workflow Release Mode, use: `âŒ Release aborted: Workflow release requires explicit release request, approved Blueprint, PASS debug report, and PASS verification report.`
- For Explicit Maintenance Release Mode, use: `âŒ Release aborted: Maintenance release requires an explicit current-turn release request, reviewed release diff, targeted validation evidence, changelog/version update, and release approval.`
- Do NOT perform version bumps, modify changelogs, commit, tag, push, or merge.

## Runtime Prompt Protocol for Release Gates

Every approval gate in **Phase 8 (Release Summary)**, **Phase 9 (Commit Release)**, and **Phase 11 (Push Branch)** MUST use native `ask_question` first when available, then fall back to the centralized runtime prompt selection protocol only if native UI prompting is unavailable:
1. First use native `ask_question` with question `Approve this release step?`, options `Continue|Cancel`, and default `Cancel`.
2. If native `ask_question` is unavailable, run:
   ```bash
   aiwf prompt select --question "Approve this release step?" --options "Continue|Cancel" --default "Cancel"
   ```
3. If the result is `Continue`, proceed to the next step. If the result is `Cancel`, stop. If the fallback returns `PROMPT_UNAVAILABLE`, no user selection occurred; use native `ask_question` if available or keep the release gate stopped.
4. Do not ask for the same approval again in plain chat text.

---

## Workflow Sequence

In autonomous mode, the Workflow Supervisor prepares the complete release plan and pauses once at the plan-bound Release Approval Gate. After approval, it follows the approved plan automatically; the Agent must not ask the user to type internal commit, tag, push, or update commands.

The release process runs in 12 sequential phases:

```
Phase 0: Automatically execute 'project-memory-update' to compile latest repository state
         ↓
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
Phase 8: Approval Gate - Present Release Summary and query user using native Agent/IDE `ask_question` first; use this CLI only as a fallback bridge:
         ```bash
         aiwf prompt select --question "Choose release action:" --options "Continue|Cancel" --default "Cancel"
         ```
         ↓
Phase 9: Commit release updates (Requires explicit approval)
         ↓
Phase 10: Compile and write Git tags (single or module-specific; no duplicates)
         ↓
Phase 11: Push branch and tags (Requires explicit approval)
         ↓
Phase 12: Install released framework into this project
         - Windows PowerShell: aiwf update -Force
         - Unix shells: aiwf update --force
         - Verify local project state after update
```

---

## Completion Contract

Upon completion, output this plain text report:

```text
Current Phase:
Phase 5 â€” Implementation to Release

Status:
Completed

Release Summary:
- Release Mode:    [single | module]
- Branch Status:   [main | master | merged]
- Affected Modules:[list of affected modules]
- Git Tag(s) Written: [vX.Y.Z | module/vX.Y.Z | none]

Recommended Next Action:
- Option A: Start a new feature or major work item (Recommended)
  1. Open a New Conversation / Chat Session.
  2. Trigger the next skill in the new session: /initialize-workflow
- Option B: Continue working in the current conversation (For hotfixes, brainstorming, or quick tweaks)
  1. Trigger one of the following skills directly in this chat:
     - /brainstorming (To brainstorm next steps or ideas)
     - /quick-feature (For minor extensions to the released feature)
     - /quick-fix (For immediate hotfixes or regression fixes)

Workflow Paused.
```

## ðŸ“ MANDATORY WALKTHROUGH UPDATE

After generating any artifact, executing code, or completing this phase, you **ABSOLUTELY MUST** write or update `.agents/state/walkthrough.md`. Document what was accomplished, which files were generated/modified, decisions made, and the next steps. This guarantees context is preserved across new chat sessions.
