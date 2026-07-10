<!-- File path: docs/designs/QUICK-020_upgrade_quick_feature_skill_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-020
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Upgrade quick-feature Skill

## 1. Proposed Code Changes

### skills/quick-feature/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật mẫu tài liệu Đặc tả Mini Spec đầu ra để tích hợp thêm 7 phần phân tích mới. Thêm chỉ dẫn phân định scope và quy tắc kiểm tra tương thích ngược hạ nguồn.
- **Changes**: Cập nhật mẫu tài liệu Markdown mẫu spec và thêm hướng dẫn chi tiết quy trình.

## 2. Target Folder Structure
```text
.
└── skills
    └── quick-feature
        └── SKILL.md
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng lên `3.2.0` cho `skills/quick-feature/SKILL.md`.

## 4. Algorithms & Key Logic
- Quy trình Động não tinh gọn được tăng cường chất lượng mà không làm mất đi tính concise.

## 5. Validation Rules
- Mini Spec được sinh ra bắt buộc không chứa absolute paths.

## 6. Implementation Checklist
- [ ] Bổ sung 7 phần phân tích mới vào tệp `skills/quick-feature/SKILL.md`.
- [ ] Bổ sung chỉ dẫn phân định scope chi tiết vào `skills/quick-feature/SKILL.md`.
- [ ] Tích hợp chỉ dẫn tương thích ngược hạ nguồn.
- [ ] Chạy thử nghiệm và chạy unit tests.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh đặc tả QUICK Spec sinh ra chứa đầy đủ 7 mục mới và không có absolute paths.
  - *REQ-002*: Xác minh kỹ năng tương thích ngược chạy bình thường trên các dự án cũ.
