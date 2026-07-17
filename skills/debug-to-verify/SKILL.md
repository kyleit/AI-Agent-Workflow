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
repository: https://gitlab.com/hngan.it/ai-workflow-skills
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
  usage: cached
---

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
Giai đoạn phải đáp ứng toàn bộ các tiêu chí kiểm duyệt dưới đây (đặc biệt là tiêu chí đường dẫn tương đối):

| # | Tiêu chí đánh giá | Trạng thái | Điều kiện đạt & Ghi chú |
|---|---|:---:|---|
| 1 | Tương thích đường dẫn | [ ] PASS | 100% đường dẫn trong mã nguồn, script, kết quả và tài liệu là đường dẫn tương đối hoặc đã được làm sạch. Không có URL tệp tuyệt đối, đường dẫn ổ đĩa, đường dẫn tuyệt đối của macOS hoặc Linux, mã xác thực hoặc log chứa đường dẫn tuyệt đối. |
| 2 | Build và chạy runtime thật | [ ] PASS | App, service, UI, CLI hoặc worker build lại thành công, runtime thật mở được, surface tích hợp thật sẵn sàng, và không còn tiến trình treo sau kiểm thử. |
| 3 | Kiểm thử runtime thật | [ ] PASS | Kiểm thử gọi vào runtime đang chạy qua surface thật phù hợp như IPC, API, UI, CLI, SDK, job queue hoặc service, không chỉ kiểm thử đơn vị hoặc phản chiếu. Luồng thành công chính, luồng lỗi hợp lệ, luồng hồi quy và dọn dẹp đều đạt. |
| 4 | Đầy đủ chức năng | [ ] PASS | Giai đoạn triển khai đủ lệnh hoặc API bắt buộc, không có phần giữ chỗ chưa hoàn thiện, không bỏ sót hành vi cũ quan trọng. |
| 5 | Dễ đọc và dễ bảo trì | [ ] PASS | Mã nguồn, script và kết quả rõ ràng, có cấu trúc, đặt tên dễ hiểu, ít trùng lặp và không lan phạm vi ngoài giai đoạn. |
| 6 | Tuân thủ rule, Memory/RAG và skill trong project | [ ] PASS | Người điều phối và tác nhân đã đọc rule trong project, ưu tiên Memory First/RAG First bằng `./.agents/skills/project-rag-search` khi cần ngữ cảnh, chọn skill phù hợp từ `./.agents/skills`, đọc hướng dẫn skill trước khi làm, ghi rule/skill trong prompt/báo cáo và không tạo bản rule hoặc skill trùng lặp ở nơi khác. |
| 7 | An toàn dữ liệu và dọn dẹp | [ ] PASS | Kiểm thử chụp nhanh và khôi phục cấu hình, không tạo rác ở Màn hình nền hoặc thư mục tạm, không lộ mã xác thực hoặc bí mật, không để lại tiến trình app hoặc kiểm thử. |
| 8 | Tuân thủ tài liệu & Truy vết | [ ] PASS | Bắt buộc chạy và đánh giá điểm chất lượng tài liệu đạt từ 95/100 điểm trở lên bằng cách sử dụng skill [document-compliance-assessment](file:///Volumes/Kyle/AgentsProject/.agents/skills/document-compliance-assessment/SKILL.md) và đính kèm báo cáo Document Compliance Report. |

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

## Đánh giá tuân thủ tài liệu (Document Compliance Report)
*(Bắt buộc hoàn thành đánh giá tài liệu bằng skill `document-compliance-assessment` trước khi đề xuất Go)*

- **Documentation Traceability Score**: <diem>/100
- **Trạng thái**: [ĐẠT | KHÔNG ĐẠT]

## 4. Go / No-Go Recommendation
- **Recommendation**: [GO | NO-GO]
- **Justification**: [Summary of reasons why this code should or should not proceed to production release. Must satisfy all checklist items to Go]

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
