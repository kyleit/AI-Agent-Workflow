<!-- docs/designs/FEAT-009_refactor_workflow_skills_blueprint.md -->

---
artifact_type: blueprint
feature_id: FEAT-009
workflow: standard
status: draft
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: ../plans/FEAT-009_refactor_workflow_skills_plan.md
next_artifact: None
---

# Technical Blueprint – Refactor AI Workflow Skills

Bản thiết kế kiến trúc kỹ thuật tối ưu hóa tệp kỹ năng thưa Ba.

## 1. Kiến trúc chung & Tham chiếu chia sẻ (Shared Capabilities)
*   **Chính sách toàn cục**: Tất cả các chính sách dùng chung như Cổng phê duyệt (Section 1), Git Workflow (Section 2), Memory First (Section 3), RAG (Section 4), Artifact (Section 5), Testing (Section 8), Release (Section 9), Validation Engine (Section 11), và Session state tracking (Section 12) đều nằm tập trung tại tài liệu chính thức [AI_RULES.md](../../AI_RULES.md).
*   **Tham chiếu tại Kỹ năng**: Mỗi tệp `SKILL.md` sẽ chỉ chứa danh sách tham chiếu ngắn đến các Section tương ứng của `AI_RULES.md`.

## 2. Tiêu chuẩn cấu trúc tệp Kỹ năng rút gọn (Standard SKILL.md Template)
Mỗi tệp `SKILL.md` sau khi refactor bắt buộc phải tuân theo cấu trúc sau để đảm bảo tính gọn nhẹ và tối ưu token:

```markdown
# Skill: [Skill Name]

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK
[Bắt buộc giữ lại kiểm tra checkpoint và mô tả chi tiết luồng cập nhật .session.json nguyên tử]
- **Yêu cầu checkpoint**: [Giá trị checkpoint]
- **Trạng thái cập nhật**:
  - Start: `status: "in_progress"`, `checkpoint`, `current_skill`, `current_command`, `current_step`, `current_logs`, `updated_at`.
  - Step logs: Ghi nhận tăng trưởng qua `current_step` và `current_logs`.
  - Completion: `status: "completed"`, `checkpoint`, `suggested_next_skill`, `suggested_next_command`.
  - Failure: `status: "failed"`.

## 🔒 GLOBAL POLICY REFERENCES
Kỹ năng này tuân thủ các chính sách chung tại [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1)
- **Memory First Policy** (Section 3)
- [Các chính sách khác liên quan]

## Multi-Agent Contract
Kỹ năng này hoạt động dưới Multi-Agent Workflow, tham chiếu đến:
- [agents/](../../agents/)
- [runtime/](../../runtime/)

## [Các phần mô tả logic nghiệp vụ đặc thù của Kỹ năng]
[Bao gồm Input, Output, Workflow Sequence đặc thù và Completion Contract]
```

## 3. Danh sách chi tiết các phần bị loại bỏ tại mỗi tệp
Con sẽ rà soát và cắt bỏ các đoạn văn bản giải thích dài dòng bị lặp lại:

1.  **Chính sách Phê duyệt & Git**: Cắt bỏ các phần hướng dẫn chi tiết cách đặt tên nhánh (`feature/FEAT-XXX`), cách kiểm tra dirty tree, và các bước Y/N xác nhận thủ công (đã có trong Section 1 & 2 của `AI_RULES.md`).
2.  **Đọc bộ nhớ & RAG**: Cắt bỏ phần hướng dẫn cách đọc `memory.config.json` theo thứ tự và cách chạy RAG (đã có trong Section 3 & 4 của `AI_RULES.md`).
3.  **Hành vi lỗi & Tệp kết quả**: Cắt bỏ các phần giải thích chung về định dạng bảng Markdown và liên kết tương đối (đã có trong Section 5 & 7 của `AI_RULES.md`).

## 4. Kế hoạch kiểm thử & Đồng bộ hóa (Verification & Synchronization)
1.  Chạy `powershell .\update.ps1 -Force` để áp dụng cấu trúc mới của 26 kỹ năng vào thư mục `.agents/skills/`.
2.  Chạy `powershell .\doctor.ps1` để đảm bảo hệ thống nhận dạng chính xác tất cả các kỹ năng và không gặp lỗi cú pháp.
3.  Thực hiện chạy thử lệnh `/initialize-workflow` hoặc `/software-development-workflow` để xác nhận tệp `.session.json` cập nhật đúng đắn.
