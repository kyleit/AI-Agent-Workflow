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
license: MIT
created_at: 2026-07-04
updated_at: 2026-07-04
description: Validate that the feature is production-ready. Enforce standards before release.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached---

# Skill: debug-to-verify

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 8 or 7"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "debug-to-verify" --command "verify" --checkpoint 9 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 9 --step "Step Complete" --next-skill "implementation-to-release" --next-command "release"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Purpose

Perform a final qualitative and quantitative audit on the active feature implementation to ensure it meets all acceptance criteria, technical design blueprints, and security/performance standards before staging for release.

---

## Responsibilities

1. **Acceptance Criteria Verification**: Cross-reference implemented features against the original criteria defined in the project plan.
2. **Blueprint Compliance**: Ensure file names, APIs, class signatures, and database schemas strictly align with the technical blueprint under `docs/features/<feature-family>/blueprints/` — either `<WORK_ITEM_ID>_<slug>_blueprint.md` (single-file shape) or `phase-NN-<phase-slug>/phase-blueprint.md` (+ its companion files) for the multi-phase shape (see `plan-to-blueprint`). Legacy flat or former work-item Blueprints may be read only for older work. Read every companion file linked from the phase index, not just the index itself.
3. **Coding Standards Audit**: Ensure correct code styles, robust error handling, proper naming conventions, and clean syntax are met.
4. **Security & Performance**: Review authentication checks, sanitize inputs, verify database indexes, and look for performance bottlenecks.
5. **Code Standard Review Evidence**: Verify that `code-standard-review` ran and passed with changed-file evidence.
6. **Real Runtime Evidence**: Verify the post-implementation report includes at least one real runtime/user case without mocks or fake test doubles when the feature has a runtime surface.
7. **Frontend Browser Evidence**: For UI/browser changes, verify screenshot evidence exists and was captured through IDE browser tools, CDP debug port, or an equivalent real browser automation path.
8. **Documentation & Changelog**: Check if user docs, API docs, and `CHANGELOG.md` edits are ready for the release notes.
9. **Final Evidence Report**: Verify `docs/features/<feature-family>/reports/<WORK_ITEM_ID>_<slug>_post_implementation_report.md` (or matching phase variant) exists and links screenshots with relative Markdown paths.
10. **Go / No-Go Decision**: Make a formal quality assessment whether the code is safe to be merged/released.

---

## Workflow Sequence

```
Step 1: Inspect session state, debug report, and visual debug report (if applicable)
        ↓
Step 2: Audit Acceptance Criteria, Blueprint compliance, and code-standard-review evidence
        ↓
Step 3: Audit targeted validation, tests, real runtime case evidence, and browser/CDP screenshots when UI is affected
        ↓
Step 4: Audit Documentation, Security, Code Quality, and Post-Implementation Evidence Report
        ↓
Step 5: Generate Verification Report at docs/features/<feature-family>/verification/<WORK_ITEM_ID>_<slug>_verify.md
        (or docs/features/<feature-family>/verification/phase-NN-<phase-slug>/phase-verify.md when verifying one phase)
        ↓
Step 6: Update session checkpoint to 9 & output heartbeat
```

---

## Output Report Format: `docs/features/<feature-family>/verification/FEAT-XXX_slug_verify.md` (or `phase-NN-<phase-slug>/phase-verify.md` — see Workflow Sequence Step 4)

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
Giai đoạn phải đáp ứng toàn bộ các tiêu chí kiểm duyệt dưới đây (đặc biệt là tiêu chí đường dẫn tương đối):

| # | Tiêu chí đánh giá | Trạng thái | Điều kiện đạt & Ghi chú |
|---|---|:---:|---|
| 1 | Tương thích đường dẫn | [ ] PASS | 100% đường dẫn trong mã nguồn, script, kết quả và tài liệu là đường dẫn tương đối hoặc đã được làm sạch. Không có URL tệp tuyệt đối, đường dẫn ổ đĩa, đường dẫn tuyệt đối của macOS hoặc Linux, mã xác thực hoặc log chứa đường dẫn tuyệt đối. |
| 2 | Build và chạy runtime thật | [ ] PASS | App, service, UI, CLI hoặc worker build lại thành công, runtime thật mở được, surface tích hợp thật sẵn sàng, và không còn tiến trình treo sau kiểm thử. |
| 3 | Kiểm thử runtime thật | [ ] PASS | Kiểm thử gọi vào runtime đang chạy qua surface thật phù hợp như IPC, API, UI, CLI, SDK, job queue hoặc service, không chỉ kiểm thử đơn vị hoặc phản chiếu. Luồng thành công chính, luồng lỗi hợp lệ, luồng hồi quy và dọn dẹp đều đạt. |
| 4 | Đầy đủ chức năng | [ ] PASS | Giai đoạn triển khai đủ lệnh hoặc API bắt buộc, không có phần giữ chỗ chưa hoàn thiện, không bỏ sót hành vi cũ quan trọng. |
| 5 | Dễ đọc và dễ bảo trì | [ ] PASS | Mã nguồn, script và kết quả rõ ràng, có cấu trúc, đặt tên dễ hiểu, ít trùng lặp và không lan phạm vi ngoài giai đoạn. |
| 6 | Code Standard Review | [ ] PASS | Bắt buộc sử dụng `code-standard-review`, có changed-file review evidence, và mọi checklist item đều PASS hoặc có failed-point loop đã sửa lại. |
| 7 | An toàn dữ liệu và dọn dẹp | [ ] PASS | Kiểm thử chụp nhanh và khôi phục cấu hình, không tạo rác ở Màn hình nền hoặc thư mục tạm, không lộ mã xác thực hoặc bí mật, không để lại tiến trình app hoặc kiểm thử. |
| 8 | Tuân thủ tài liệu & Truy vết | [ ] PASS | Bắt buộc chạy và đánh giá điểm chất lượng tài liệu đạt từ 95/100 điểm trở lên bằng cách sử dụng skill [document-compliance-assessment](../../.agents/skills/document-compliance-assessment/SKILL.md) và đính kèm báo cáo Document Compliance Report. |
| 9 | Final Evidence Report | [ ] PASS | `docs/features/<feature-family>/reports/<WORK_ITEM_ID>_<slug>_post_implementation_report.md` or a phase variant exists, includes review/validation/debug/real runtime/browser evidence, and all screenshots use relative Markdown links. |
| 10 | Browser Screenshot Evidence | [ ] PASS | Nếu UI/browser bị ảnh hưởng, có screenshot thực tế được chụp bằng IDE browser tools hoặc CDP/equivalent real browser automation. |

## 3. Điều kiện bắt buộc đánh FAIL (NO-GO)
Giai đoạn phải bị đánh FAIL (NO-GO) nếu gặp bất kỳ lỗi nào dưới đây (báo cáo đánh giá bị vô hiệu):
1. Có đường dẫn tuyệt đối thật trong mã nguồn, script, kết quả hoặc tài liệu thuộc phạm vi giai đoạn.
2. Build thất bại.
3. Ứng dụng không mở được.
4. Surface tích hợp thật của runtime không sẵn sàng (ví dụ: IPC token/pipe, API endpoint, UI route, CLI command, SDK entrypoint hoặc service health).
5. Ca kiểm thử runtime chính thất bại.
6. Kiểm thử chỉ là kiểm thử đơn vị hoặc phản chiếu (reflection) mà chưa gọi vào runtime thật.
7. Có tiến trình app hoặc kiểm thử còn treo sau khi kiểm thử kết thúc.
8. Kết quả chứa mã xác thực, bí mật hoặc dữ liệu chưa được làm sạch.
9. Có luồng tự ý tắt app, service hoặc runtime trong khi luồng điều phối chính chưa cho phép.
10. Chưa đủ bằng chứng thực tế nhưng báo cáo đạt.
11. Bỏ qua các skill phù hợp sẵn có trong `./.agents/skills` mà không có lý do được chấp nhận.
12. Tự ý copy hoặc tạo bản sao skill, prompt hoặc workflow mới ở thư mục khác khi project đã có skill tương ứng.
13. Bỏ qua rule của project hoặc không chứng minh đã đọc rule bắt buộc.
14. Tạo rule song song làm lệch hướng `PROJECT_RULES.md`, `./.agents/AGENTS.md` hoặc `./.agents/AI_RULES.md`.
15. Quét mã nguồn hoặc hỏi thiết kế trước khi tra cứu Project Memory và dùng `./.agents/skills/project-rag-search` khi cần ngữ cảnh.
16. Thiếu `code-standard-review` evidence cho các file đã thay đổi.
17. Thiếu post-implementation evidence report trong `docs/reports/`.
18. UI/browser thay đổi nhưng không có screenshot evidence từ browser thật hoặc CDP/equivalent.
19. Real runtime case chỉ dùng mock, fake data, reflection, hoặc unit test mà không gọi surface thật.

## Đánh giá tuân thủ tài liệu (Document Compliance Report)
*(Bắt buộc hoàn thành đánh giá tài liệu bằng skill `document-compliance-assessment` trước khi đề xuất Go)*

- **Documentation Traceability Score**: <diem>/100
- **Trạng thái**: [ĐẠT | KHÔNG ĐẠT]

## Code Standard Review Evidence

| Field | Evidence |
|---|---|
| Skill Used | `code-standard-review` |
| Changed Files Reviewed | `relative/path`, `relative/path` |
| Result | [PASS | FAIL] |
| Failed Points | `None` or exact failed-point list |

## Post-Implementation Evidence Report

- **Report Path**: `docs/features/<feature-family>/reports/FEAT-XXX_slug_post_implementation_report.md`
- **Real Runtime Case Result**: [PASS | FAIL | Not Applicable + why]
- **Browser Evidence Result**: [PASS | FAIL | Not Applicable + why]
- **Screenshot Links**:
  - `docs/reports/assets/FEAT-XXX_slug/screenshot.png`

## 4. Go / No-Go Recommendation
- **Recommendation**: [GO | NO-GO]
- **Justification**: [Summary of reasons why this code should or should not proceed to production release. Must satisfy all checklist items to Go]

## 4. Remaining Risks
- **Risk**: [Risk] → **Mitigation**: [Mitigation]

## 5. Verification Status
**Status**: [PASS | FAIL (Cannot Release)]
```

If verification status is **FAIL**, the workflow is stopped and blocked from releasing. Return to the debug phase.

Verification MUST be FAIL if the post-implementation evidence report is missing, `code-standard-review` evidence is missing, real runtime evidence is missing for changed runtime behavior, or screenshot/CDP evidence is missing for UI/browser changes.

---

## Completion Contract

```text
Current Phase:
Phase 8 — Feature Verification

Status:
Completed

Report Generated:
docs/features/<feature-family>/verification/FEAT-XXX_slug_verify.md (or phase-NN-<phase-slug>/phase-verify.md)

Verification Status:
[PASS | FAIL]

Recommended Next Skill:
implementation-to-release (command: /release)
```
