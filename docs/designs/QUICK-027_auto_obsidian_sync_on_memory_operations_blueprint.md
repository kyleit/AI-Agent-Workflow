<!-- File path: docs/designs/QUICK-027_auto_obsidian_sync_on_memory_operations_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-027
workflow: quick-feature
status: approved
---
# Technical Design Blueprint – Auto Obsidian Sync on Memory Operations

## 1. Proposed Code Changes

Chúng ta sẽ chỉnh sửa các tệp tin liên quan đến tiến trình bootstrap và update bộ nhớ dự án để tích hợp tự động đồng bộ sang Obsidian.

### [bootstrap.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/bootstrap.py)
- **Operation**: MODIFY
- **Responsibility**: Khởi tạo cấu trúc bộ nhớ dự án.
- **Changes**:
  - Nhập thêm `log_warn` từ module `common`.
  - Tích hợp khối lệnh gọi hàm `sync("obsidian")` của `knowledge-runtime` ở cuối hàm `run_bootstrap` trước khi hoàn tất phiên làm việc.

### [update.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/update.py)
- **Operation**: MODIFY
- **Responsibility**: Cập nhật bộ nhớ dự án tăng cường dựa trên Git diff hoặc mốc thời gian.
- **Changes**:
  - Tích hợp khối lệnh gọi hàm `sync("obsidian")` của `knowledge-runtime` ở cuối hàm `run_update` trước khi hoàn tất phiên làm việc.

---

## 2. Target Folder Structure
Mô hình cấu trúc các tệp tin thay đổi trong dự án:
```text
.
├── runtime/
│   └── scripts/
│       └── project_memory/
│           ├── bootstrap.py
│           └── update.py
└── docs/
    ├── quick/
    │   └── QUICK-027_auto_obsidian_sync_on_memory_operations.md
    └── designs/
        └── QUICK-027_auto_obsidian_sync_on_memory_operations_blueprint.md
```

---

## 3. Interface & Data Contracts
- **API/CLI Contracts**: Các lệnh của `project-memory` CLI giữ nguyên:
  - `python3 runtime/scripts/project_memory/cli.py bootstrap`
  - `python3 runtime/scripts/project_memory/cli.py update [--full]`

---

## 4. Algorithms & Key Logic
Khối lệnh tự động đồng bộ hóa Obsidian:
```python
# Tự động đồng bộ sang Obsidian qua knowledge-runtime
try:
    try:
        import knowledge_runtime
    except ImportError:
        import sys
        framework_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        kr_scripts = os.path.join(framework_root, "skills", "knowledge-runtime", "scripts")
        if kr_scripts not in sys.path:
            sys.path.append(kr_scripts)
        import knowledge_runtime
    
    # Kích hoạt đồng bộ Obsidian
    sync_res = knowledge_runtime.sync("obsidian")
    if sync_res.get("status") == "success":
        log_success("Obsidian sync completed automatically.")
    else:
        log_warn(f"Obsidian auto-sync returned status: {sync_res.get('message')}")
except Exception as e:
    log_warn(f"Auto-sync Obsidian skipped: {e}")
```

---

## 5. Validation Rules
- Đảm bảo xử lý an toàn: Nếu import `knowledge_runtime` thất bại hoặc ném ra biệt lệ khi đang đồng bộ, chương trình sẽ in log cảnh báo và tiếp tục trả về trạng thái `"success"` của tiến trình bộ nhớ chính.

---

## 6. Implementation Checklist
- [x] Cập nhật import `log_warn` trong `bootstrap.py`.
- [x] Tích hợp logic tự động đồng bộ vào `bootstrap.py`.
- [x] Tích hợp logic tự động đồng bộ vào `update.py`.
- [x] Cập nhật assert trong test suite `test_provider_manager.py`.

---

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *QUICK-027-REQ-001*: Chạy `python3 runtime/scripts/project_memory/cli.py bootstrap` -> Thấy log thành công `Obsidian sync completed automatically after memory bootstrap.`.
  - *QUICK-027-REQ-002*: Chạy `python3 runtime/scripts/project_memory/cli.py update` -> Thấy log thành công `Obsidian sync completed automatically after memory update.`.
  - *QUICK-027-REQ-003*: Chạy `pytest skills/knowledge-runtime/tests/ skills/workflow-runtime/tests/test_project_memory.py` -> Đảm bảo toàn bộ 23/23 tests PASS.
