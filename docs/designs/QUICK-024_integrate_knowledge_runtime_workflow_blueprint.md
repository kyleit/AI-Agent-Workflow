<!-- File path: docs/designs/QUICK-024_integrate_knowledge_runtime_workflow_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-024
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Integrate knowledge-runtime Across the Entire AIWF Workflow

## 1. Proposed Code Changes

### skills/knowledge-runtime/SKILL.md
- **Operation**: NEW
- **Responsibility**: Đặc tả Kỹ năng `knowledge-runtime` đầy đủ 10 phần theo quy chế bắt buộc Skill Skeleton mới của QUICK-023.
- **Changes**: Tạo tệp mới.

### skills/knowledge-runtime/tests/test_knowledge_runtime.py
- **Operation**: NEW
- **Responsibility**: Di chuyển tệp kiểm thử tự động của gói tri thức từ `skills/workflow-runtime/tests/` sang đây.
- **Changes**: Tạo tệp mới và di chuyển mã kiểm thử.

### skills/workflow-runtime/tests/test_knowledge_runtime.py
- **Operation**: DELETE
- **Responsibility**: Xóa tệp kiểm thử ở vị trí cũ để tránh trùng lặp.
- **Changes**: Xóa tệp.

### AI_RULES.md
- **Operation**: MODIFY
- **Responsibility**: Bổ sung quy tắc cấm các Kỹ năng tự ý kết nối Provider trực tiếp mà phải thông qua `Knowledge Runtime` làm tầng trung gian duy nhất.
- **Changes**: Cập nhật điều khoản số 23.

### AGENTS.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật danh mục Agent và bổ sung mô tả về Knowledge Runtime làm tầng dữ liệu hợp nhất.
- **Changes**: Thêm mô tả.

### README.md
- **Operation**: MODIFY
- **Responsibility**: Cập nhật sơ đồ kiến trúc và tài liệu hướng dẫn chung của dự án.
- **Changes**: Cập nhật phần RAG/Memory.

## 2. Target Folder Structure
```text
.
├── AI_RULES.md
├── AGENTS.md
├── README.md
└── skills
    └── knowledge-runtime
        ├── SKILL.md
        ├── scripts
        │   └── knowledge_runtime
        │       ├── __init__.py
        │       ├── api.py
        │       ├── cache.py
        │       ├── index.py
        │       ├── analyzer.py
        │       └── providers
        │           ├── __init__.py
        │           ├── base.py
        │           ├── markdown.py
        │           ├── sqlite.py
        │           ├── vector.py
        │           └── obsidian.py
        └── tests
            └── test_knowledge_runtime.py
```

## 3. Interface & Data Contracts
- **YAML Frontmatter Version**: Cập nhật phiên bản kỹ năng `knowledge-runtime` lên `1.0.0`.

## 4. Implementation Checklist
- [ ] Tạo tệp `skills/knowledge-runtime/SKILL.md` đầy đủ 10 phần.
- [ ] Tạo tệp `skills/knowledge-runtime/tests/test_knowledge_runtime.py` chứa mã kiểm thử cũ.
- [ ] Xóa tệp `skills/workflow-runtime/tests/test_knowledge_runtime.py`.
- [ ] Cập nhật `AI_RULES.md` thêm quy tắc bắt buộc tri thức.
- [ ] Cập nhật `AGENTS.md` và `README.md`.
- [ ] Chạy thử nghiệm và chạy unit tests.

## 5. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Xác minh `pytest skills/knowledge-runtime/tests/test_knowledge_runtime.py` chạy thành công.
  - *REQ-002*: Xác minh dự án không còn tệp `skills/workflow-runtime/tests/test_knowledge_runtime.py`.
  - *REQ-003*: Xác minh `AI_RULES.md` có đầy đủ quy tắc tích hợp.
