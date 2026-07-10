<!-- File path: docs/designs/FEAT-025_project_workflow_templates_blueprint.md -->

---
feature_id: FEAT-025
feature_name: Project-specific Workflow Templates & Release Configuration
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-025_project_workflow_templates_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Project-specific Workflow Templates & Release Configuration

## 0. Baseline Context & References
- **Memory Baseline**: project-summary.md indicates active SDLC tracking via .session.json. Confidence: High.
- **RAG Query Summaries**: Found session.py, workflow_runtime.py, and release_manager.py as core scripts managing checkpoints and actions.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/session.py` (L19-L75)
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (L1668-L1681)
  - `skills/workflow-runtime/scripts/release_manager.py` (L7-L53)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/release_manager.py` | `MODIFY` | Đọc cấu hình quy trình tùy biến và thực thi các câu lệnh phát hành tùy biến được khai báo. | `subprocess`, `session` | Thấp. Nếu lỗi trong cấu hình lệnh, kịch bản sẽ báo lỗi thoát an toàn. |
| `skills/workflow-runtime/scripts/session.py` | `MODIFY` | Bổ sung hàm đọc cấu hình `.agents/workflow.config.json` để trích xuất thông tin Git Flow và Release. | `json`, `os` | Thấp. Tự động trả về giá trị mặc định nếu tệp cấu hình không tồn tại. |
| `.agents/templates/workflow.config.json.template` | `NEW` | Cung cấp tệp cấu hình mẫu mô tả cấu trúc nhánh Git và các commands phát hành cho dự án. | None | Không có. |

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── MANIFEST.json
│   ├── release.config.json
│   ├── state
│   │   ├── context.json
│   │   ├── rules.json
│   │   └── session.json
│   └── templates
│       └── workflow.config.json.template
├── docs
│   ├── brainstorming
│   │   └── FEAT-025_project_workflow_templates.md
│   ├── designs
│   │   └── FEAT-025_project_workflow_templates_blueprint.md
│   └── plans
│       └── FEAT-025_project_workflow_templates_plan.md
└── skills
    └── workflow-runtime
        └── scripts
            ├── release_manager.py
            └── session.py
```

## 3. Interface Contracts (Public & Internal)

### Public Interface Contracts
- **Configuration Schema** (`.agents/workflow.config.json`):
```json
{
  "project_name": "string",
  "git_flow": {
    "development_branch": "string (default: main)",
    "release_branch": "string (default: main)",
    "feature_prefix": "string (default: feature/FEAT-)",
    "sync_method": "string (merge | rebase, default: merge)",
    "extra_push_branches": "array of strings (default: [])"
  },
  "release_pipeline": {
    "steps": "array of strings (default: [bump_version, update_changelog, git_commit, git_tag, git_push])",
    "custom_commands": {
      "module_name": "array of strings (default: [])",
      "global": "array of strings (default: [])"
    }
  }
}
```

- **Backward Compatibility**: Nếu không có file cấu hình tùy biến, hệ thống sẽ sử dụng cấu hình mặc định (development_branch="main", release_branch="main", sync_method="merge", custom_commands=[]).

### Internal Component Contracts
- **Session Module** (`skills/workflow-runtime/scripts/session.py`):
```python
def load_workflow_config() -> dict[str, object]:
    """
    Nạp cấu hình workflow.config.json từ thư mục .agents/.
    Trả về cấu hình mặc định nếu file không tồn tại hoặc lỗi cú pháp JSON.
    """
```

- **Release Manager** (`skills/workflow-runtime/scripts/release_manager.py`):
```python
def run_release_execute(approve: bool = False) -> dict[str, object]:
    """
    Thực thi các bước phát hành theo cấu hình release_pipeline.steps.
    Hỗ trợ thực hiện các lệnh shell được cấu hình trong custom_commands.
    """
```

## 4. Algorithms & Logic Specifications

### Custom Command Execution (Release Manager)
1. Đọc tệp `.agents/workflow.config.json` thông qua `load_workflow_config()`.
2. Xác định danh sách các modules bị ảnh hưởng bằng cách so sánh thay đổi qua `git status --porcelain`.
3. Cho mỗi bước trong `release_pipeline.steps`:
   - Nếu bước là `"custom_commands"`:
     - Lấy danh sách lệnh trong `custom_commands[module_name]` cho các modules bị ảnh hưởng.
     - Lấy danh sách lệnh trong `custom_commands["global"]`.
     - Thực thi từng lệnh trong môi trường subprocess.
     - Nếu một lệnh trả về mã lỗi khác 0, hủy tiến trình phát hành lập tức để bảo vệ Git repository.

## 5. State Machine & Transitions
Không thay đổi máy trạng thái của Checkpoint. Giữ nguyên Checkpoint 1 đến 10.

## 6. Validation and Safety Constraints
- **Shell Command Sanitization**: Để tránh việc chạy các lệnh nguy hiểm (như `rm -rf /`), toàn bộ lệnh custom chỉ được chạy khi:
  1. Người dùng chạy CLI với cờ `--approve` (hoặc thông qua chốt duyệt Choice).
  2. Lệnh được hiển thị tường minh trên màn hình trước khi thực thi.

## 7. Backward Compatibility & Migration Mapping
Không thay đổi lược đồ dữ liệu của `.session.json`. Cấu hình workflow mới được lưu trữ trong một tệp cấu hình độc lập bên ngoài.

## 8. Implementation Checklist
- [ ] Xây dựng tệp mẫu `.agents/templates/workflow.config.json.template`.
- [ ] Triển khai hàm `load_workflow_config` trong `skills/workflow-runtime/scripts/session.py`.
- [ ] Cập nhật `run_release_execute` trong `skills/workflow-runtime/scripts/release_manager.py` để đọc và thực thi các câu lệnh phát hành tùy biến.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Đọc cấu hình workflow mặc định khi file không tồn tại | Trả về cấu hình mặc định an toàn | Chạy unit test kiểm tra hàm `load_workflow_config` | `skills/workflow-runtime/tests/test_runtime.py` test_load_workflow_config_defaults |
| `REQ-002` | Đọc cấu hình workflow tùy biến từ tệp JSON | Trả về các nhánh Git và lệnh custom đúng như khai báo | Tạo tệp config tạm và chạy test kiểm tra hàm | `skills/workflow-runtime/tests/test_runtime.py` test_load_workflow_config_custom |
| `REQ-003` | Thực thi lệnh custom trong pha Release | Các câu lệnh shell custom (ví dụ: `echo "hello"`) được chạy thành công | Chạy thực tế `workflow_runtime.py release execute --approve` | Kiểm tra log console xuất ra dòng chữ "hello" |

## 10. Disallowed Outputs Validation
- [x] No `file://` or absolute paths used.
- [x] No placeholders like `...` or `etc.` in code/structures.
- [x] No `TBD` or `To Be Determined` placeholders.
- [x] No unsafe permission values (e.g. `unrestricted`).
- [x] No unmapped legacy fields without migration rules.
