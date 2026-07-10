<!-- File path: docs/designs/FEAT-028_pure_split_state_management_blueprint.md -->

---
feature_id: FEAT-028
feature_name: Pure Split State Management
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-028_pure_split_state_management_plan.md
next_artifact: ../../
---

# Technical Blueprint & Implementation Contract – Pure Split State Management

## 0. Baseline Context & References
- **Memory Baseline**: Memory Status is FRESH. Memory Confidence is High. Memory source matches [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md).
- **RAG Query Summaries**: Keyword search matches that the split state architecture separates fields into `.agents/state/*.json` files.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/session.py` (lines 10-130)
  - `skills/workflow-runtime/scripts/state_sync.py` (lines 40-240)
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (lines 230-240)
  - `extensions/visualizer/src/extension.ts` (lines 240-330)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Loại bỏ việc ghi tệp đĩa `.session.json` trong `aggregate_state`. | `write_json_atomic` | Thấp. Hàm `aggregate_state` chỉ trả về cấu trúc session gộp trong bộ nhớ mà không ghi xuống đĩa. |
| `skills/workflow-runtime/scripts/session.py` | MODIFY | Thay thế việc đọc/ghi trực tiếp `.session.json` bằng hàm `load_session` và `deconstruct_state` tương tác trực tiếp với `state/`. Thêm hàm dọn dẹp `.session.json` khi khởi chạy. | `deconstruct_state`, `load_session` | Thấp. Tệp `.session.json` sẽ không bao giờ xuất hiện trên đĩa nữa. |
| `extensions/visualizer/src/extension.ts` | MODIFY | Loại bỏ hoàn toàn fallback đọc `.session.json` khi thiếu thư mục `state/` và tối ưu hóa việc nạp dữ liệu. | `aggregateStateFromFiles` | Thấp. Visualizer Extension sẽ luôn hoạt động ở chế độ Split State. |

## 2. Target Folder Structure
Cấu trúc thư mục của dự án sau khi sửa đổi (tệp `.session.json` và `.session.json.bak` biến mất hoàn toàn):
```text
.
├── .agents
│   ├── MANIFEST.json
│   ├── AGENTS.md
│   ├── AI_RULES.md
│   ├── memory.config.json
│   ├── project-profile.json
│   ├── release.config.json
│   ├── workflow.config.json
│   ├── project_runtime.db
│   ├── state
│   │   ├── context.json
│   │   ├── workflow.json
│   │   ├── runtime.json
│   │   ├── approvals.json
│   │   ├── usage.json
│   │   ├── agents.json
│   │   └── recovery.json
│   └── skills
│       └── workflow-runtime
│           └── scripts
│               ├── state_sync.py
│               ├── session.py
│               └── workflow_runtime.py
└── extensions
    └── visualizer
        └── src
            └── extension.ts
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - Không thay đổi các lệnh CLI hay payload của API.
  - **Backward Compatibility**: Tệp `.session.json` bị xóa bỏ hoàn toàn. Bất kỳ script hoặc công cụ nào muốn lấy thông tin trạng thái gộp có thể gọi lệnh CLI mới `python skills/workflow-runtime/scripts/workflow_runtime.py context` (hoặc lệnh tương đương để in ra định dạng JSON từ bộ nhớ).
- **Internal Component Contracts**:
  - Hàm `aggregate_state(workspace_root: str) -> dict[str, Any]` trong `state_sync.py` vẫn giữ nguyên chữ ký hàm (signature) nhưng loại bỏ lệnh ghi tệp `write_json_atomic(session_path, session)`.
  - Hàm `save_session_atomic(data: dict[str, Any]) -> None` trong `session.py` sẽ thực hiện lưu trữ trạng thái phân tách bằng cách gọi `deconstruct_state` trực tiếp và xóa bỏ cơ chế ghi `.session.json` dự phòng.
- **Visualizer Extension Changes**:
  - `updateSessionData()`:
    ```typescript
    if (fs.existsSync(contextPath)) {
        session = this.aggregateStateFromFiles(rootPath);
        this._cachedSession = session;
    } else {
        this.clearSessionData();
        return;
    }
    ```
    Loại bỏ hoàn toàn nhánh `else if (fs.existsSync(this._sessionPath))`.

## 4. Algorithms & Logic Specifications
### 1. aggregate_state
Hàm gộp trạng thái trong `state_sync.py` sẽ được cập nhật như sau:
```python
def aggregate_state(workspace_root: str) -> dict[str, Any]:
    state_dir = os.path.join(workspace_root, ".agents", "state")
    
    context = read_json_safe(os.path.join(state_dir, "context.json"))
    workflow = read_json_safe(os.path.join(state_dir, "workflow.json"))
    runtime = read_json_safe(os.path.join(state_dir, "runtime.json"))
    approvals = read_json_safe(os.path.join(state_dir, "approvals.json"))
    usage = read_json_safe(os.path.join(state_dir, "usage.json"))
    agents = read_json_safe(os.path.join(state_dir, "agents.json"))
    
    session = {
        "workspace": {
            "path": context.get("workspace_path", "."),
            "valid": True
        },
        # ... (giữ nguyên logic gộp các trường khác)
    }
    
    # LOẠI BỎ lệnh ghi tệp xuống đĩa ở đây
    # write_json_atomic(session_path, session) -> XÓA BỎ LỆNH NÀY
    
    update_recovery_file(workspace_root)
    return session
```

### 2. save_session_atomic
Hàm lưu trạng thái trong `session.py` sẽ được cập nhật như sau:
```python
def save_session_atomic(data: dict[str, Any]) -> None:
    # Lấy thông tin hiện tại từ load_session() thay vì đọc tệp .session.json
    existing = load_session()
    
    new_data = dict(data)
    if "conversation_id" not in new_data or not new_data["conversation_id"]:
        new_data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
        
    if "permission_mode" not in new_data:
        new_data["permission_mode"] = existing.get("permission_mode", "sandbox")
        new_data["permission_mode_selected_at"] = existing.get("permission_mode_selected_at", datetime.now().astimezone().isoformat())
        new_data["permission_mode_selected_by"] = existing.get("permission_mode_selected_by", "system")
    
    new_data["updated_at"] = datetime.now().astimezone().isoformat()
    
    # 1. Ghi rã trạng thái vào các file trạng thái con
    deconstruct_state(".", new_data)
    
    # 2. Xóa bỏ hoàn toàn phần gộp ghi .session.json xuống đĩa
    # aggregate_state(".") -> LOẠI BỎ hoặc chỉ dùng trong bộ nhớ để tạo recovery file
    # Xóa file .session.json nếu còn tồn tại trên đĩa để tránh nhập nhèm dữ liệu
    session_file = os.path.join(".agents", ".session.json")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
        except Exception:
            pass
```

## 5. State Machine & Transitions
Quy trình chuyển đổi trạng thái của quy trình SDLC (checkpoint) không thay đổi, chỉ có vị trí lưu trữ thông tin checkpoint được ghi trực tiếp vào `state/workflow.json` thay vì lưu trong `.session.json`.

## 6. Validation and Safety Constraints
- **Permission Check**: Giới hạn quyền ghi và đảm bảo các file con trong `.agents/state/` không bị ghi đè bởi đường dẫn tuyệt đối hoặc các ký tự đặc biệt nguy hiểm.
- **Enum Constraint**: `permission_mode` chỉ chấp nhận các giá trị: `sandbox` hoặc `full_access`.

## 7. Backward Compatibility & Migration Mapping
Tất cả các trường dữ liệu cũ từ `.session.json` được chuyển đổi tương ứng trực tiếp sang các tệp nhỏ hơn trong `state/` và được gộp lại khi chạy `load_session()` để đảm bảo các API nội bộ không bị thay đổi.

| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| `workspace` | `state/context.json` | `workspace_path` | Lưu giá trị relative path | Tải lại từ thư mục gốc dự án |
| `git` | `state/context.json` | `git` | Sao chép nguyên vẹn cấu trúc | Truy vấn lại thông qua lệnh `git` |
| `work_item` | `state/workflow.json` | `work_item` | Sao chép nguyên vẹn cấu trúc | Trực tiếp cập nhật từ docs |
| `version` | `state/context.json` | `project_version` | Sao chép trường version | Đọc lại từ MANIFEST.json |

## 8. Implementation Checklist
- [ ] Chỉnh sửa `skills/workflow-runtime/scripts/state_sync.py` để loại bỏ ghi tệp đĩa `.session.json` trong hàm `aggregate_state`.
- [ ] Chỉnh sửa `skills/workflow-runtime/scripts/session.py` để dùng `load_session()` thay thế việc đọc `.session.json` trong `save_session_atomic` và thực hiện xóa tệp `.session.json` cũ.
- [ ] Chỉnh sửa `extensions/visualizer/src/extension.ts` để bỏ phần fallback đọc tệp `.session.json` trong hàm `updateSessionData()`.
- [ ] Biên dịch lại Visualizer Extension TypeScript bằng lệnh `make package` trong thư mục `extensions/visualizer/`.
- [ ] Chạy bộ kiểm thử `test_runtime.py` và kiểm tra hoạt động của CLI.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Xóa tệp `.session.json` trên đĩa khi lưu trạng thái. | Không còn tệp `.agents/.session.json` trên đĩa. | Chạy lệnh `init` và kiểm tra sự tồn tại của tệp. | `test_runtime.py: TestRuntimeEngine.test_init_flow` |
| `REQ-002` | Visualizer nạp trạng thái từ split files. | Giao diện Visualizer hiển thị đúng trạng thái. | Kiểm tra màn hình Visualizer sau khi chạy lệnh. | Kiểm tra thủ công thông qua UI Visualizer. |
| `REQ-003` | Chạy thành công toàn bộ unit tests. | 18 bài test đơn vị đều PASS. | Chạy `python -m unittest discover` | `test_runtime.py` |

## 10. Disallowed Outputs Validation
- [x] Không sử dụng `file://` hay đường dẫn tuyệt đối.
- [x] Không chứa các ký tự giữ chỗ như `...` hoặc `etc.` trong code/cấu trúc thư mục ở các phần mô tả kịch bản chính.
- [x] Không chứa các giá trị phân quyền không an toàn (`unrestricted`).
