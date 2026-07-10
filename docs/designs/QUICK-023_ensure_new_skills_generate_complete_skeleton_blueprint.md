<!-- File path: docs/designs/QUICK-023_ensure_new_skills_generate_complete_skeleton_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-023
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Ensure New Skills Always Generate a Complete AIWF Skill Skeleton

## 1. Proposed Code Changes

### skills/plan-to-blueprint/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Bổ sung quy tắc bắt buộc vào `Output Rules` và `Constraints` quy định rằng khi có một Kỹ năng mới được khai báo tạo dưới `skills/<skill-name>/`, bản thiết kế bắt buộc phải sinh ra tệp `skills/<skill-name>/SKILL.md` và các thư mục hỗ trợ đi kèm.
- **Changes**: Cập nhật phần hướng dẫn đầu ra.

### AI_RULES.md
- **Operation**: MODIFY
- **Responsibility**: Bổ sung chính sách bắt buộc vào phần quy định chung (Global Policies) của `AI_RULES.md` để đảm bảo tính nhất quán trên toàn bộ hệ thống đại lý.
- **Changes**: Thêm điều khoản số 12 trong `AI_RULES.md`.

## 2. Target Folder Structure
```text
.
├── AI_RULES.md
└── skills
    └── plan-to-blueprint
        └── SKILL.md
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng lên `3.2.0` cho `skills/plan-to-blueprint/SKILL.md` (giữ nguyên để giữ tính đồng bộ).

## 4. Algorithms & Key Logic
- Quy trình kiểm tra điều kiện đầu ra của Architect:
  ```text
  [Khai báo new skill] ──> check if skills/<skill-name>/SKILL.md exists in write_set
                                 ├── [Yes] ──> Validation Pass
                                 └── [No]  ──> Validation Fail & STOP
  ```

## 5. Validation Rules
- Bản thiết kế tạo kỹ năng mới nhưng thiếu `SKILL.md` hoặc các thư mục bắt buộc sẽ bị đánh giá thất bại (Validation Fail).

## 6. Implementation Checklist
- [ ] Cập nhật tệp `skills/plan-to-blueprint/SKILL.md` thêm quy tắc bắt buộc Skill Skeleton.
- [ ] Cập nhật tệp `AI_RULES.md` thêm điều khoản 12.
- [ ] Chạy thử nghiệm và chạy unit tests.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh Architect từ chối sinh blueprint nếu có new skill dưới `skills/` mà không khai báo tệp `SKILL.md`.
  - *REQ-002*: Xác minh tệp `AI_RULES.md` được cập nhật chính xác điều khoản 12.
