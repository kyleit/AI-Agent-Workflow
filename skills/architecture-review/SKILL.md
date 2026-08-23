---
name: architecture-review
command: audit-arch
aliases:
  - arch-review
  - check-arch
category: architecture
tags:
  - architecture
  - design
  - review
  - compliance
version: 1.1.0
license: MIT
created_at: 2026-07-17
updated_at: 2026-07-29
review_type_required: true
review_type_facade: true
supported_review_types:
  - FEASIBILITY
  - PLAN_ARCHITECTURE
  - BLUEPRINT_APPROVAL
  - FINAL_CONFORMANCE
description: Đánh giá kiến trúc thiết kế giải pháp thiết lập trước khi tạo Technical Design Blueprint.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
---

# Skill: Architecture Review

---

## 📐 Structural Architecture Review Contract (4 Distinct Review Types)

The `architecture-review` skill requires an explicit `review_type` input parameter. Generic reviews without a specified `review_type` MUST NOT be processed (`BLOCKED_NEEDS_REVIEW_TYPE`).

Supported Review Types:
1. **`FEASIBILITY`** (Architecture Feasibility Review — Post-Brainstorming feasibility audit)
2. **`PLAN_ARCHITECTURE`** (Plan Architecture Review — Post-Execution Plan task decomposition audit)
3. **`BLUEPRINT_APPROVAL`** (Blueprint Architecture Approval — Post-Blueprint zero-placeholder freeze audit)
4. **`FINAL_CONFORMANCE`** (Final Architecture Conformance Review — Post-Implementation zero-drift audit)

---

Đánh giá và kiểm định thiết kế kiến trúc hệ thống của kế hoạch triển khai (Implementation Plan) trước khi viết Technical Design Blueprint nhằm đảm bảo tính tuân thủ, độ tin cậy và không vi phạm các ranh giới thiết kế toàn cục.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

Skill này kết nối trực tiếp với AIWF Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint**: Xác nhận checkpoint hiện tại trước khi thực thi.
- **Tiến trình**:
  - *Start*: `aiwf start --skill "architecture-review" --command "audit-arch" --checkpoint 3 --step "Starting architecture review..."`
  - *Complete*: `aiwf complete --checkpoint 3 --step "Architecture Review Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"`

---

## 📐 Architecture Compliance Score (Thang điểm 100)

Để được phê duyệt thông qua cổng kiểm soát kiến trúc, giải pháp thiết kế phải đạt tối thiểu **95/100** điểm và không vi phạm bất kỳ điều kiện NO-GO nào dưới đây.

| # | Tiêu chí đánh giá | Điểm tối đa | Điều kiện đạt đủ điểm & Ghi chú |
|---|---|---:|---|
| 1 | Ranh giới Module | 25 | Mã nguồn, API hoặc logic không được lấn sang các module không liên quan. Tuân thủ nguyên tắc Single Responsibility Principle (SRP) ở cấp độ kiến trúc. |
| 2 | Tính tương thích Runtime | 20 | Tích hợp chính xác với AIWF Workflow Runtime và các cơ chế trạng thái, không xung đột luồng xử lý hoặc thiết lập cổng trùng lặp. |
| 3 | Chiều phụ thuộc (Dependency) | 20 | Luồng phụ thuộc đi đúng hướng (các module tầng dưới không được phép phụ thuộc ngược chiều vào module tầng trên). |
| 4 | Hợp đồng giao tiếp (Contracts) | 20 | Thiết lập rõ ràng các giao diện API, SDK, CLI hoặc các ranh giới tương tác dữ liệu. |
| 5 | Không vi phạm quy tắc chung | 15 | Không sử dụng đường dẫn tuyệt đối, không có cấu hình cứng nhạy cảm (secrets), và tuân thủ các quy định chung của dự án. |
| | **Tổng điểm** | **100** | **Điểm đạt tối thiểu để đi tiếp: 95/100** |

---

## 🛑 Điều kiện bắt buộc đánh FAIL (NO-GO)

Giải pháp sẽ bị đánh FAIL (NO-GO) và chặn đứng quy trình ngay lập tức nếu:
1. Vi phạm quy tắc đường dẫn tuyệt đối trong thiết kế hoặc cấu hình.
2. Có luồng phụ thuộc ngược (Circular Dependency) hoặc phụ thuộc sai tầng kiến trúc.
3. Thiết kế có chứa mã xác thực, khóa bảo mật hoặc thông tin nhạy cảm được cấu hình cứng.
4. Lấn ranh giới hệ thống, can thiệp vào các tệp tin lõi được bảo vệ mà không được định nghĩa rõ ràng trong Mini Spec/Plan.
5. Thiết kế đề xuất tạo thêm tệp tin rule song song hoặc copy lại các module/skill sẵn có gây phân mảnh hệ thống.
6. **Lỗi Kế Thừa Giai Đoạn Trước (Cascading Upstream Defect)**: Phát hiện tài liệu đầu vào của giai đoạn trước (`Spec`, `Brainstorming`, hoặc `Roadmap`) có sai sót, mâu thuẫn ranh giới, mơ hồ về phạm vi hoặc vi phạm quy chuẩn mà chưa được khắc phục tận gốc.

---

## 🛡️ Anti-Cascading Failure & Upstream Review Guard (Chặn Lỗi Dây Chuyền)

> [!CRITICAL]
> **QUY TẮC BẢO TOÀN KIẾN TRÚC NGƯỢC (BACKWARD CONSISTENCY INVARIANT)**:
> Mọi sai sót nhỏ ở giai đoạn trước (Spec/Brainstorming/Plan) nếu không được rà soát và phát hiện kịp thời sẽ bị khuếch đại theo cấp số nhân ở các giai đoạn sau (Blueprint/Implementation/Testing), dẫn đến **"Sai một ly, đi một dặm - Toàn bộ hệ thống phía sau bị sụp đổ"**.
> 
> Vì vậy, trước khi chấp nhận tạo tài liệu ở giai đoạn hiện tại, Agent **BẮT BUỘC PHẢI THỰC HIỆN 3 BƯỚC RÀ SOÁT ĐẦU VÀO**:
> 1. **Kiểm Tra Tính Nhất Quán Ngược (Upstream Consistency)**: Đối chiếu từng yêu cầu kỹ thuật của giai đoạn trước xem có mâu thuẫn với cấu trúc thực tế của codebase hay không.
> 2. **Kiểm Tra Ranh Giới Phạm Vi (Scope Drift Interceptor)**: Đảm bảo tài liệu trước không tự ý thêm bớt tính năng ngoài phạm vi yêu cầu của người dùng.
> 3. **Quy Tắc Dừng Khẩn Cấp (Halt & Fix Root-Cause)**: Nếu phát hiện tài liệu giai đoạn trước có lỗi, **BẮT BUỘC PHẢI DỪNG LẠI (HALT)**, từ chối tạo tài liệu tiếp theo, và yêu cầu sửa chữa tài liệu trước đó cho đến khi đạt điểm tuyệt đối. Tuyệt đối không được "chữa cháy tạm bợ" ở giai đoạn sau.

---

## Strict Reviewer Accountability

Architecture Review is a hard gate. The reviewer MUST NOT approve an artifact merely because the author reports completion, because a checklist is present, or because continuing the workflow would be convenient. The reviewer MUST inspect the actual artifact content and cite concrete evidence from artifact sections, tables, paths, traceability matrices, phase coverage, and path hygiene checks.

A review MUST return `NO-GO` when the artifact is thin, vague, incomplete, inconsistent with the roadmap/brainstorming/plan/blueprint chain, missing master+phase coverage where required, missing `Internal Review Evidence`, missing relative-path evidence, or unsupported by concrete references.

### Blueprint Review Non-Negotiables

For `BLUEPRINT_APPROVAL`, the reviewer must independently verify the blueprint against the real source tree and the preceding roadmap, brainstorming, and plan artifacts. A PASS is forbidden when any of these are true:

- the blueprint says `Data Schemas & Models`, `Targeted Test Strategy`, `Risk Mitigation`, or `Acceptance Criteria` passed but the matching section is missing or only generic;
- the blueprint's file-by-file matrix conflicts with current source files or omits files mentioned by the plan;
- code blocks are illustrative only and do not include concrete signatures, state fields, error paths, and implementation sequence;
- the review uses a perfect score without citing exact blueprint headings, rows, source paths, and failed-point repair history;
- the review ignores local path contamination, encoding corruption, or traceability links that are not project-relative;
- the review approves test evidence where the command output shows no test files or no behavioral tests.

When these conditions occur, output `NO-GO`; do not "approve with notes". A blueprint approval review is a stop gate, not an advisory memo.

When returning `NO-GO`, the reviewer MUST list exact failed points only. Each failed point MUST include:
- Artifact path.
- Section, table, or field that fails.
- Violated policy, requirement, or architecture rule.
- Why the current content is insufficient.
- Minimum correction required before re-review.

The reviewer MUST NOT rewrite the whole artifact, broaden scope, or approve partial fixes. On re-review, the reviewer MUST verify each failed point directly and record `Fixed`, `Still Failing`, or `Regressed`.

---

## 📝 Mẫu báo cáo nghiệm thu (Architecture Review Report)

Báo cáo kết quả phải được ghi lại tại `docs/architecture-reviews/<feature-slug>/FEAT-XXX_architecture_review.md`, trước khi tiếp tục giai đoạn lập Blueprint:

```markdown
# Architecture Review Report – [FEAT-XXX]

- **Feature ID**: FEAT-XXX
- **Maturity level**: [Draft | Reviewed | Approved]
- **Date**: YYYY-MM-DD
- **Reviewer**: Antigravity / Architecture Specialist

## 1. Executive Summary
[Tóm tắt ngắn gọn các phát hiện kiến trúc và đánh giá chung về tính khả thi]

## 2. Scorecard Details
- **Ranh giới Module**: /25
- **Tính tương thích Runtime**: /20
- **Chiều phụ thuộc**: /20
- **Hợp đồng giao tiếp**: /20
- **Không vi phạm quy tắc chung**: /15
- **Tổng điểm**: /100 (Yêu cầu >= 95/100 để thông qua)

## 3. Go / No-Go Recommendation
- **Recommendation**: [GO | NO-GO]
- **Justification**: [Lý do phê duyệt hoặc từ chối thiết kế kiến trúc hiện tại]

## 4. Remediation Items
*(Bắt buộc liệt kê nếu có tiêu chí chưa đạt điểm tối đa hoặc cần điều chỉnh)*
- **Item 1**: [Mô tả chi tiết và giải pháp khắc phục]
```
