<!-- File path: docs/designs/QUICK-019_upgrade_brainstorming_to_plan_skill_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-019
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Upgrade brainstorming-to-plan Skill

## 1. Proposed Code Changes

### skills/brainstorming-to-plan/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật mẫu tài liệu Kế hoạch thực hiện đầu ra để bổ sung 11 phần phân tích tri thức mới của v3.2. Bổ sung hướng dẫn Planner tự động xuất thêm tệp JSON cấu trúc kế hoạch (`FEAT-XXX_plan.json`).
- **Changes**: Cập nhật mẫu tài liệu Markdown và thêm phần đặc tả cấu trúc tệp JSON đầu ra trong tệp hướng dẫn.

### skills/plan-to-blueprint/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Hướng dẫn Architect ưu tiên tìm đọc tệp cấu trúc JSON `docs/plans/FEAT-XXX_feature_slug_plan.json` trước khi đọc tệp Markdown để tiết kiệm token và tăng tốc độ xử lý.
- **Changes**: Cập nhật Step 1 của quy trình thiết kế blueprint.

## 2. Target Folder Structure
```text
.
└── skills
    ├── brainstorming-to-plan
    │   └── SKILL.md
    └── plan-to-blueprint
        └── SKILL.md
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng lên `3.2.0` cho `skills/brainstorming-to-plan/SKILL.md`.
- **JSON Plan Schema (`FEAT-XXX_plan.json`)**:
  - `phases`: Mảng các phase thực hiện.
  - `tasks`: Danh sách các task (id, description, effort, owner, operations, files).
  - `dependencies`: Bản đồ hoặc danh sách phụ thuộc.
  - `parallel_groups`: Các nhóm task có thể chạy song song.
  - `exit_criteria`: Các điều kiện nghiệm thu.
  - `rollback`: Các bước rollback.
  - `tests`: Các kịch bản kiểm thử.

## 4. Algorithms & Key Logic
- Quy trình nạp thông tin tối ưu hoá ở hạ nguồn:
  ```text
  [Planner] ──(Tạo)──> docs/plans/FEAT-XXX_plan.json
                              │
                              ▼
  [Architect] ──(Ưu tiên đọc)─┘ (Giảm tải token parsing)
  ```

## 5. Validation Rules
- Tệp JSON cấu trúc sinh ra bắt buộc phải hợp lệ (valid JSON) và khớp hoàn toàn các Task ID và File paths với tệp Markdown kế hoạch tương ứng. Cấm tuyệt đối sinh đường dẫn tuyệt đối.

## 6. Implementation Checklist
- [ ] Cập nhật tệp `skills/brainstorming-to-plan/SKILL.md` thêm 11 phần phân tích mới.
- [ ] Bổ sung chỉ dẫn tạo tệp JSON trong `skills/brainstorming-to-plan/SKILL.md`.
- [ ] Cập nhật chỉ dẫn nạp của `skills/plan-to-blueprint/SKILL.md` để đọc tệp JSON.
- [ ] Chạy thử nghiệm quy trình và unit tests.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh Planner sinh ra cả tệp MD và JSON kế hoạch khớp nhau.
  - *REQ-002*: Xác minh tệp JSON kế hoạch không chứa absolute paths.
  - *REQ-003*: Xác minh Architect v3.2 ưu tiên đọc hiểu tệp JSON kế hoạch thành công.
