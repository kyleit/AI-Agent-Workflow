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
version: 1.0.0
license: MIT
created_at: 2026-07-17
updated_at: 2026-07-17
description: Đánh giá kiến trúc thiết kế giải pháp thiết lập trước khi tạo Technical Design Blueprint.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none---

# Skill: Architecture Review

Đánh giá và kiểm định thiết kế kiến trúc hệ thống của kế hoạch triển khai (Implementation Plan) trước khi viết Technical Design Blueprint nhằm đảm bảo tính tuân thủ, độ tin cậy và không vi phạm các ranh giới thiết kế toàn cục.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

Skill này bắt buộc phải kết nối với Python CLI Runtime Engine:
- **Validate Checkpoint**: Xác nhận checkpoint hiện tại trước khi thực thi.
- **Tiến trình**:
  - *Start*: `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "architecture-review" --command "audit-arch" --checkpoint 3 --step "Starting architecture review..."`
  - *Complete*: `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Architecture Review Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"`

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

---

## 📝 Mẫu báo cáo nghiệm thu (Architecture Review Report)

Báo cáo kết quả phải được ghi lại tại `docs/architecture-reviews/<feature-slug>/FEAT-XXX_architecture_review.md` (đúng thư mục thật đang dùng trong dự án — không phải `docs/reviews/`), trước khi tiếp tục giai đoạn lập Blueprint. Với plan multi-phase, có thể review từng phase riêng tại `docs/architecture-reviews/<feature-slug>/phase-NN-<phase-slug>/` nếu master-level review là chưa đủ cho phase đó, nhưng mặc định 1 review cho toàn bộ master plan là đủ (feature-wide architecture properties thường không đổi theo từng phase — xem ghi chú "Scope note" trong ví dụ đã có tại `docs/architecture-reviews/backend-api-gateway/`):

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
