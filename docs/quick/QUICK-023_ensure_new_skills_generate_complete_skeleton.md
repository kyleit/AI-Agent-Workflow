<!-- File path: docs/quick/QUICK-023_ensure_new_skills_generate_complete_skeleton.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-023
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Ensure New Skills Always Generate a Complete AIWF Skill Skeleton

## 1. Feature Goal
Khắc phục lỗ hổng quy trình thiết kế kỹ thuật khi sinh các Kỹ năng (Skills) mới. Bắt buộc mọi Bản thiết kế (Technical Blueprint) khi khai báo tạo mới một kỹ năng (dưới thư mục `skills/<skill-name>/`) phải định nghĩa và sinh ra toàn bộ bộ khung (Skeleton) hoàn chỉnh bao gồm tệp tin hướng dẫn cốt lõi `SKILL.md` (chứa đầy đủ 10 mục đặc tả) và các thư mục hỗ trợ bắt buộc như `scripts/`, `tests/`. Bản thiết kế không tuân thủ sẽ tự động thất bại khi xác thực (validation fail).

## 2. Scope
- **In Scope**:
  - Cập nhật tệp [skills/plan-to-blueprint/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/plan-to-blueprint/SKILL.md):
    - Khai báo quy chế bắt buộc tạo mới Skill Skeleton khi tạo thư mục dưới `skills/<skill-name>/`.
    - Định nghĩa cấu trúc 10 mục của `SKILL.md` bắt buộc cho Kỹ năng mới (Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations).
    - Thêm quy tắc validation: Bản thiết kế tạo kỹ năng mới nhưng thiếu đặc tả `SKILL.md` sẽ bị đánh dấu thất bại.
  - Cập nhật tệp [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md):
    - Bổ sung điều khoản chính sách bắt buộc: "Whenever a Blueprint introduces a new AIWF Skill, it MUST generate the complete Skill skeleton including SKILL.md and all required supporting artifacts."
- **Out of Scope**: Thay đổi logic CLI Python của `workflow_runtime.py`.
