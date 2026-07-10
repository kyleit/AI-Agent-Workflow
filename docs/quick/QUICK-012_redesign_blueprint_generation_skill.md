<!-- File path: docs/quick/QUICK-012_redesign_blueprint_generation_skill.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-012
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Redesign the Blueprint Generation Skill

## 1. Feature Goal
Cải tiến và tái thiết kế kỹ năng Tạo Thiết Kế Kỹ Thuật (Blueprint Generation Skill) trong AI Workflow Framework. Mục tiêu cốt lõi là nâng cấp tài liệu Design Blueprint từ một tài liệu thiết kế mức cao (high-level) thành một **Hợp đồng Triển khai** (Implementation Contract) chặt chẽ, chi tiết, không chứa placeholder và không mơ hồ. 

Tài liệu Blueprint mới phải đảm bảo một AI hoặc lập trình viên khác có thể thực thi viết code trực tiếp mà không cần đưa ra bất kỳ quyết định kiến trúc nào khác, và không phải đoán mò bất kỳ chi tiết triển khai nào.

## 2. Scope

- **In Scope**:
  - Cập nhật tài liệu hướng dẫn và template Blueprint trong `plan-to-blueprint/SKILL.md` (Kỹ năng chính tạo Blueprint cho các tính năng chuẩn).
  - Cập nhật template Blueprint tại Step 7 trong `quick-feature/SKILL.md` và `quick-fix/SKILL.md` (Các kỹ năng xử lý nhanh).
  - Cập nhật quy tắc chất lượng Blueprint trong `AI_RULES.md` tại Section 10 (Workflow Phase Separation Policy) và Section 13 (Blueprint Mandatory Execution Policy) để thắt chặt các tiêu chuẩn chất lượng đầu ra.
  
- **Out of Scope**:
  - Không sửa đổi logic code python trong `workflow_runtime.py`.
  - Không thay đổi các Skill khác không liên quan trực tiếp đến việc tạo Blueprint (như `environment-bootstrap`, `initialize-workflow`, v.v.).
