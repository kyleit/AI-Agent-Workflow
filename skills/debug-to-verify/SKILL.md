---
name: debug-to-verify
command: verify
aliases:
  - check
  - audit
category: workflow
tags:
  - verification
  - quality
  - compliance
version: 1.0.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-04
updated_at: 2026-07-04
description: Validate that the feature is production-ready. Enforce standards before release.
---

# Skill: debug-to-verify

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification**.
Verify that the current checkpoint in `.session.json` is `8` (Frontend Visual Debug Complete) for UI features, or `7` (Debug Complete) for backend-only features.
1. If the visual debug report `docs/verification/FEAT-XXX_visual_debug.md` exists and has `status: FAIL`, the verification audit MUST fail immediately. Release is blocked.
2. If the session file is missing, if context health is `broken`, or if the current checkpoint is less than `7` (or less than `8` for frontend features):
   - Recommend running: `implementation-to-debug` or `frontend-visual-debug` to reach the correct checkpoint state.
   - Stop execution.
3. At the start of execution, update `.session.json` checkpoint to `9` (Verification Complete) and set `"status"` to `"in_progress"`.
4. Upon successful verification validation and generation of the report, update `.session.json` checkpoint to `9` (Verification Complete), set `"status"` to `"completed"`, and output the runtime heartbeat.
5. If verification fails, set `"status"` to `"failed"`.

---

## Purpose

Perform a final qualitative and quantitative audit on the active feature implementation to ensure it meets all acceptance criteria, technical design blueprints, and security/performance standards before staging for release.

---

## Responsibilities

1. **Acceptance Criteria Verification**: Cross-reference implemented features against the original criteria defined in the project plan.
2. **Blueprint Compliance**: Ensure file names, APIs, class signatures, and database schemas strictly align with the technical blueprint (`docs/designs/FEAT-XXX_*.md`).
3. **Coding Standards Audit**: Ensure correct code styles, robust error handling, proper naming conventions, and clean syntax are met.
4. **Security & Performance**: Review authentication checks, sanitize inputs, verify database indexes, and look for performance bottlenecks.
5. **Documentation & Changelog**: Check if user docs, API docs, and `CHANGELOG.md` edits are ready for the release notes.
6. **Go / No-Go Decision**: Make a formal quality assessment whether the code is safe to be merged/released.

---

## Workflow Sequence

```
Step 1: Inspect session state, debug report, and visual debug report (if applicable)
        ↓
Step 2: Audit Acceptance Criteria & Blueprint compliance
        ↓
Step 3: Audit Documentation, Security, and Code Quality
        ↓
Step 4: Generate Verification Report at docs/verification/FEAT-XXX_verify.md
        ↓
Step 5: Update session checkpoint to 9 & output heartbeat
```

---

## Output Report Format: `docs/verification/FEAT-XXX_verify.md`

Generate the verification report using this Markdown template:

```markdown
---
artifact_type: verification
feature_id: FEAT-XXX
workflow: standard
status: [PASS | FAIL]
---

# Verification Report – [Feature Title]

## 1. Executive Summary
[Brief description of the verification activities and audit outcome]

## 2. Verification Checklist
| Quality Gate Item | Status | Verification Details |
| :--- | :---: | :--- |
| **Acceptance Criteria** | [PASS | FAIL] | [Notes on validation tests] |
| **Blueprint Compliance** | [PASS | FAIL] | [Check file layouts and interfaces] |
| **Coding Standards** | [PASS | FAIL] | [Check naming, error checks, formatting] |
| **Security Audits** | [PASS | FAIL] | [Input sanitization, permissions check] |
| **Performance Check** | [PASS | FAIL] | [No resource leaks, fast DB queries] |
| **Tests Coverage** | [PASS | FAIL] | [Existing test validation] |
| **Documentation & Changelog**| [PASS | FAIL] | [Verify changelog readiness] |

## 3. Go / No-Go Recommendation
- **Recommendation**: [GO | NO-GO]
- **Justification**: [Summary of reasons why this code should or should not proceed to production release]

## 4. Remaining Risks
- **Risk**: [Risk] → **Mitigation**: [Mitigation]

## 5. Verification Status
**Status**: [PASS | FAIL (Cannot Release)]
```

If verification status is **FAIL**, the workflow is stopped and blocked from releasing. Return to the debug phase.

---

## Completion Contract

```text
Current Phase:
Phase 8 — Feature Verification

Status:
Completed

Report Generated:
docs/verification/FEAT-XXX_verify.md

Verification Status:
[PASS | FAIL]

Recommended Next Skill:
implementation-to-release (command: /release)
```
