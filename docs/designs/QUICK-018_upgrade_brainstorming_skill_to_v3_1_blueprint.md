<!-- File path: docs/designs/QUICK-018_upgrade_brainstorming_skill_to_v3_1_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-018
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Upgrade Brainstorming Skill to v3.1

## 1. Proposed Code Changes

### skills/brainstorming/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật mẫu tài liệu Động não đầu ra để tích hợp thêm 10 phần phân tích v3.1 mới. Đồng thời, thiết lập quy tắc cấm sinh đường dẫn tuyệt đối (absolute paths) trong mẫu đầu ra của mô hình.
- **Changes**: Cập nhật mẫu tài liệu Markdown trong tệp hướng dẫn.

### skills/brainstorming-to-plan/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Điều chỉnh chỉ dẫn Planner kế thừa trực tiếp các phần MoSCoW, ROI và Stakeholders để phân chia các Phase lập lịch công việc chính xác.
- **Changes**: Điều chỉnh văn bản chỉ dẫn quy trình lập kế hoạch.

### skills/plan-to-blueprint/SKILL.md
- **Operation**: MODIFY
- **Responsibility**: Điều chỉnh chỉ dẫn Architect kế thừa trực tiếp Ma trận truy vết (Traceability Matrix), Luồng dữ liệu (Data Flow), Sơ đồ phụ thuộc (Dependency Graph) và Sổ đăng ký quyết định (Open Decision Register) để sinh thiết kế chi tiết.
- **Changes**: Điều chỉnh văn bản chỉ dẫn quy trình thiết kế blueprint.

## 2. Target Folder Structure
```text
.
└── skills
    ├── brainstorming
    │   └── SKILL.md
    ├── brainstorming-to-plan
    │   └── SKILL.md
    └── plan-to-blueprint
        └── SKILL.md
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng lên `3.1.0` trong frontmatter của cả 3 tệp tin kỹ năng.
- **Spec Schema Properties**: Giữ nguyên tính tương thích ngược cho các tài liệu Động não cũ.

## 4. Algorithms & Key Logic
- Khai báo mẫu cấu trúc Động não v3.1 để các Skill hạ nguồn kế thừa trực tiếp:
  - Planner trích xuất MoSCoW để lên lịch phase.
  - Architect trích xuất Traceability Matrix và Data Flow để sinh blueprint.

## 5. Validation Rules
- Cấm tuyệt đối mô hình AI sinh ra các tiền tố absolute path (`file:///`, `C:\`, `/Users/`) trong mẫu tài liệu Động não đầu ra. Mọi liên kết file phải là đường dẫn tương đối (ví dụ `skills/brainstorming/SKILL.md` thay vì `file:///path/to/SKILL.md`).

## 6. Implementation Checklist
- [ ] Bổ sung 10 phần cấu trúc phân tích v3.1 vào tệp `skills/brainstorming/SKILL.md`.
- [ ] Áp dụng quy tắc cấm sinh đường dẫn tuyệt đối trong `skills/brainstorming/SKILL.md`.
- [ ] Cập nhật chỉ dẫn tinh giản Planner trong `skills/brainstorming-to-plan/SKILL.md`.
- [ ] Cập nhật chỉ dẫn tinh giản Architect trong `skills/plan-to-blueprint/SKILL.md`.
- [ ] Chạy thử nghiệm và chạy lại các unit tests.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh tệp Động não v3.1 được sinh ra chứa đầy đủ 10 mục phân tích mới và không chứa bất kỳ đường dẫn tuyệt đối `file:///` nào.
  - *REQ-002*: Xác minh Planner v3.1 đọc hiểu MoSCoW từ Spec v3.1 thành công.
  - *REQ-003*: Xác minh Architect v3.1 đọc hiểu Ma trận truy vết từ Spec v3.1 thành công.
