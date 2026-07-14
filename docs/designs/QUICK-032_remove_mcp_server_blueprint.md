<!-- File path: docs/designs/QUICK-032_remove_mcp_server_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-032
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Remove MCP Server and Keep Logical Workflow

## 1. Proposed Code Changes
Thay đổi sẽ được áp dụng nhằm xóa bỏ hoàn toàn MCP server/adapters/manager và làm sạch runtime scripts.

### [skills/workflow-runtime/scripts/session_bootstrap_guard.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/session_bootstrap_guard.py)
- **Operation**: MODIFY
- **Responsibility**: Loại bỏ tiến trình tự động cài đặt MCP wrapper khi khởi tạo session.
- **Changes**:
  - Xóa bỏ khối `try...except` liên quan đến `Auto-provision MCP tools for Antigravity IDE` từ dòng 30 đến 45 trong hàm `initialize_workspace`.

### [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Loại bỏ lệnh `mcp` khỏi giao diện CLI của runtime.
- **Changes**:
  - Xóa bỏ hàm `do_mcp(args)` (khoảng dòng 3736 - 3765).
  - Xóa parser `mcp_p` và các subcommand của nó (install, uninstall, status, doctor) (khoảng dòng 5471 - 5484).
  - Loại bỏ entry `"mcp": do_mcp` khỏi dictionary `cmds` trong hàm `main()` (dòng 5618).
  - Loại bỏ `"mcp"` khỏi danh sách `modifying_actions` (dòng 5621).

### [skills/workflow-runtime/mcp/](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/mcp)
- **Operation**: DELETE
- **Responsibility**: Xóa toàn bộ thư mục chứa MCP server/manager code.

### [skills/workflow-runtime/adapters/](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/adapters)
- **Operation**: DELETE
- **Responsibility**: Xóa toàn bộ thư mục chứa MCP adapters.

### [skills/workflow-runtime/tests/test_antigravity_workflow_adapter.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_antigravity_workflow_adapter.py)
- **Operation**: DELETE
- **Responsibility**: Xóa file kiểm thử adapter MCP.

### [skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py)
- **Operation**: DELETE
- **Responsibility**: Xóa file kiểm thử MCP antigravity.

### [skills/workflow-runtime/tests/test_mcp_manager.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/tests/test_mcp_manager.py)
- **Operation**: DELETE
- **Responsibility**: Xóa file kiểm thử MCP manager.

---

## 2. Target Folder Structure
Sau khi xóa bỏ, cấu trúc thư mục `skills/workflow-runtime/` sẽ không còn `mcp/` và `adapters/`:
```text
skills/workflow-runtime/
├── scripts/
│   ├── session_bootstrap_guard.py (MODIFY)
│   ├── workflow_runtime.py (MODIFY)
│   └── ...
├── tests/
│   ├── test_antigravity_workflow_adapter.py (DELETE)
│   ├── test_mcp_antigravity_adapter.py (DELETE)
│   ├── test_mcp_manager.py (DELETE)
│   └── ...
└── ...
```

---

## 3. Interface & Data Contracts
Không có API/CLI contracts nào cho MCP được duy trì. Lệnh `mcp` sẽ bị loại bỏ hoàn toàn khỏi CLI.

---

## 4. Algorithms & Key Logic
Chỉ khôi phục lại các logic khởi chạy và parse CLI thuần túy của workflow runtime mà không có can thiệp của MCP.

---

## 5. Validation Rules
- Lệnh `workflow_runtime.py mcp` phải gây ra lỗi parser (`invalid choice: 'mcp'`).
- Không có module `mcp` nào được import hay sử dụng trong runtime scripts.

---

## 6. Implementation Checklist
- [ ] Xóa logic check/install MCP trong `session_bootstrap_guard.py`.
- [ ] Xóa `do_mcp` và parser cấu hình `mcp` trong `workflow_runtime.py`.
- [ ] Xóa các thư mục `mcp/` và `adapters/`.
- [ ] Xóa các file test MCP: `test_antigravity_workflow_adapter.py`, `test_mcp_antigravity_adapter.py`, `test_mcp_manager.py`.
- [ ] Chạy unit tests kiểm thử không hồi quy cho phần còn lại.

---

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Lệnh `mcp` không còn trong trợ giúp CLI (`python skills/workflow-runtime/scripts/workflow_runtime.py -h`).
  - *REQ-002*: Chạy `pytest` trên thư mục tests, tất cả các bài test (ngoại trừ các bài test đã xóa) phải PASS.
