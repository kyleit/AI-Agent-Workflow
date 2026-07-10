<!-- File path: docs/designs/QUICK-021_upgrade_plan_to_blueprint_skill_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-021
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Upgrade plan-to-blueprint Skill

## 1. Proposed Code Changes

### skills/plan-to-blueprint/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật mẫu tài liệu Bản thiết kế kỹ thuật (Technical Blueprint) đầu ra thành Hợp đồng triển khai (Implementation Contract) v3.2. Bổ sung hướng dẫn Architect tự động xuất thêm tệp JSON cấu trúc của blueprint (`FEAT-XXX_blueprint.json`).
- **Changes**: Cập nhật mẫu tài liệu Markdown và thêm phần đặc tả cấu trúc tệp JSON đầu ra trong tệp hướng dẫn.

### skills/blueprint-to-implementation/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Hướng dẫn Coder/Developer ưu tiên tìm đọc tệp cấu trúc JSON `docs/designs/FEAT-XXX_feature_slug_blueprint.json` trước khi đọc tệp Markdown để tiết kiệm token và tăng tốc độ xử lý khi lập trình.
- **Changes**: Cập nhật Step 1 của quy trình triển khai mã nguồn.

## 2. Target Folder Structure
```text
.
└── skills
    ├── plan-to-blueprint
    │   └── SKILL.md
    └── blueprint-to-implementation
        └── SKILL.md
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng lên `3.2.0` cho `skills/plan-to-blueprint/SKILL.md`.
- **JSON Blueprint Schema (`FEAT-XXX_blueprint.json`)**:
  - `modules`: Danh sách các module với classes, interfaces, public/internal methods, dependencies.
  - `configuration`: Schema, migration, defaults, validation rules.
  - `database`: Tables, indexes, relationships, constraints, migrations.
  - `cache`: Keys, invalidation, TTL, hash strategy.
  - `errors`: Exceptions, triggers, recovery, retry.
  - `skill_integration`: Before/after hooks, runtime calls.
  - `cli_runtime`: Commands, syntax, output, exit codes.
  - `sequence_flows`: Normal execution, cache miss, provider unavailable, migration.
  - `security`: Workspace boundary, path validation, sandbox rules.
  - `test_matrix`: Traceable requirements to unit/integration/stress tests.
  - `traceability`: Traceability link arrays.
  - `file_contracts`: File purpose, owner, inputs, outputs, risks.

## 4. Algorithms & Key Logic
- Quy trình nạp thông tin tối ưu hoá ở hạ nguồn:
  ```text
  [Architect] ──(Tạo)──> docs/designs/FEAT-XXX_blueprint.json
                                 │
                                 ▼
  [Coder] ──────(Ưu tiên đọc)────┘ (Lập trình chính xác)
  ```

## 5. Validation Rules
- Tệp JSON cấu trúc sinh ra bắt buộc phải hợp lệ (valid JSON) và khớp hoàn toàn các Class, Method, Database Schema, và File paths với tệp Markdown thiết kế tương ứng. Cấm tuyệt đối sinh đường dẫn tuyệt đối.

## 6. Implementation Checklist
- [ ] Cập nhật tệp `skills/plan-to-blueprint/SKILL.md` thêm 13 phần phân tích mới.
- [ ] Bổ sung chỉ dẫn tạo tệp JSON trong `skills/plan-to-blueprint/SKILL.md`.
- [ ] Cập nhật chỉ dẫn nạp của `skills/blueprint-to-implementation/SKILL.md` để đọc tệp JSON.
- [ ] Chạy thử nghiệm và chạy unit tests.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh Architect sinh ra cả tệp MD và JSON thiết kế khớp nhau.
  - *REQ-002*: Xác minh tệp JSON thiết kế không chứa absolute paths.
  - *REQ-003*: Xác minh Coder v3.2 ưu tiên đọc hiểu tệp JSON thiết kế thành công.
