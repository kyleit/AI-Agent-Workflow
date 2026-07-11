<!-- File path: docs/designs/FEAT-054_update_source_and_interactive_initialization_blueprint.md -->

---
feature_id: FEAT-054
feature_name: Build update-source and Interactive Project Initialization
status: reviewed
stage: blueprint
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../plans/FEAT-054_update_source_and_interactive_initialization_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Build update-source and Interactive Project Initialization

## 0. Baseline Context & References
- **Memory Baseline**: Tích hợp trực tiếp vào hệ thống lệnh của CLI wrapper `bootstrap.ps1` và Python Core.
- **RAG Query Summaries**: Phân tách logic update-source (cho framework gốc) và update (cho dự án vệ tinh).
- **Inspected Source Files**:
  - `bootstrap.ps1`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation (Create/Modify/Delete/Rename) | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `bootstrap.ps1` | MODIFY | Cập nhật routing `update-source` và `init` cùng hướng dẫn trợ giúp | None | Low |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Tích hợp subcommands và route sang helper classes mới | None | Low |
| `skills/workflow-runtime/scripts/update_source.py` | NEW | Lớp `SourceRepositoryService` xử lý Git logic an toàn | None | Low |
| `skills/workflow-runtime/scripts/init_wizard.py` | NEW | Lớp `InitQuestionnaire`, `RecommendationEngine`, `ScaffoldPlanner` | None | Low |

## 2. Target Folder Structure
```text
.
├── bootstrap.ps1
└── skills/
    └── workflow-runtime/
        └── scripts/
            ├── workflow_runtime.py
            ├── update_source.py
            └── init_wizard.py
```

## 3. Complete Class & Module Design
- **Class / Module Name**: `SourceRepositoryService`
  - **Responsibilities**: Kiểm tra và cập nhật mã nguồn framework qua Git an toàn.
  - **Constructor Parameters**: `source_path: str`, `remote: str = "origin"`, `branch: str = "main"`
  - **Public Methods**:
    - `check_status() -> dict`: Trả về trạng thái Git hiện tại (dirty, diverged, behind, ahead).
    - `fetch_updates() -> bool`: Fetch cập nhật từ thượng nguồn.
    - `pull_ff() -> bool`: Thực hiện `git pull --ff-only`.
  - **Internal Methods**:
    - `_is_dirty() -> bool`
    - `_is_diverged() -> bool`
- **Class / Module Name**: `InitQuestionnaire`
  - **Responsibilities**: Quản lý bộ câu hỏi wizard tương tác và lưu draft state atomic.
  - **Constructor Parameters**: `project_path: str`
  - **Public Methods**:
    - `run_interactive() -> dict`: Kích hoạt bộ câu hỏi tương tác.
    - `save_draft(state: dict)`: Lưu trạng thái câu hỏi dở dang.
    - `load_draft() -> dict`: Tải trạng thái nháp.

## 4. Detailed Interface Contracts
- **API Signature**: `def update_source(args) -> int`
  - **Parameters**: `args` (cli options)
  - **Return Types**: `int` (Exit code: 0 thành công/up-to-date, 1 lỗi)
- **API Signature**: `def init_project(args) -> int`
  - **Parameters**: `args` (cli options)
  - **Return Types**: `int` (Exit code: 0 thành công, 1 lỗi)

## 5. Configuration Schema
- Tệp tin cấu hình dự án mới được sinh tại `.agents/project.config.json` theo định dạng chuẩn hóa:
```json
{
  "schema_version": "1.0.0",
  "project": {
    "name": "string",
    "version": "string"
  },
  "topology": {},
  "architecture": {},
  "languages": [],
  "backend": {},
  "frontend": {},
  "database": {},
  "infrastructure": {},
  "security": {},
  "observability": {},
  "testing": {},
  "git": {},
  "documentation": {},
  "aiwf": {},
  "modules": [],
  "created_at": "string",
  "updated_at": "string"
}
```

## 6. Database & Storage Design
- Không có thay đổi CSDL hoặc cấu trúc bảng nào khác.

## 7. Cache Architecture
- Không áp dụng.

## 8. Error Model
- **Exception Class**: `GitCommandError`
  - **Trigger Condition**: Lệnh Git chạy thất bại hoặc có xung đột.
  - **Recovery Strategy**: Hủy tác vụ và trả về lỗi chi tiết cho người dùng.
- **Exception Class**: `InitInterruptedException`
  - **Trigger Condition**: Người dùng hủy ngang wizard khởi tạo.
  - **Recovery Strategy**: Lưu nháp state vào `.aiwf-init/state.json` và thoát an toàn.

## 9. Skill Integration Contracts
- Không có.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `aiwf update-source [--source PATH] [--remote REMOTE] [--branch BRANCH] [--check] [--dry-run] [--json] [--yes]`
- **Command Syntax**: `aiwf init [name] [--path PATH] [--non-interactive] [--config CONFIG_PATH] [--dry-run] [--resume]`

## 11. Sequence Flows
- **Normal Update-Source Flow**:
  1. Người dùng chạy `aiwf update-source`
  2. Hệ thống kiểm tra trạng thái Git cục bộ của repo framework
  3. Nếu sạch (clean) và có bản cập nhật mới, thực hiện `fetch` và hiển thị preview
  4. Yêu cầu người dùng duyệt ➔ thực thi `git pull --ff-only`

## 12. Security & Safety
- **Workspace Boundary**: Chỉ thao tác trong các thư mục được chỉ định rõ ràng qua tham số `--path` hoặc thư mục dự án hiện hành.
- **Path Validation**: Ngăn chặn ký tự thoát `../` để ghi file ngoài sandbox.

## 13. Complete Test Matrix
| Requirement ID | Test Type (Unit/Integration/Compatibility/Regression/Performance/Stress/E2E) | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `skills/workflow-runtime/tests/unit/test_update_source.py` | `update_source.py` | `self.assertEqual(res, 0)` |
| `FR-02` | Unit Test | `skills/workflow-runtime/tests/unit/test_update_source.py` | `update_source.py` | Trả lỗi khi repo bị dirty |
| `FR-05` | Unit Test | `skills/workflow-runtime/tests/unit/test_init_wizard.py` | `init_wizard.py` | Sinh cấu hình đầy đủ |
| `FR-07` | Integration Test | `skills/workflow-runtime/tests/integration/test_cli_init_integration.py` | `init_wizard.py` | Khởi tạo dự án mẫu thành công |

## 14. Requirement Traceability Matrix
- `FR-01` ➔ Task 1.2 ➔ Class `SourceRepositoryService` ➔ `update_source.py` ➔ `test_update_source.py`
- `FR-05` ➔ Task 2.2 ➔ Class `InitQuestionnaire` ➔ `init_wizard.py` ➔ `test_init_wizard.py`

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/update_source.py`
  - **Purpose**: Đóng gói các logic check trạng thái Git thượng nguồn của framework.
  - **Owner**: Architect
- **File**: `skills/workflow-runtime/scripts/init_wizard.py`
  - **Purpose**: Đóng gói logic wizard câu hỏi, khuyến nghị công nghệ và trình render tệp tin cấu hình.
  - **Owner**: Coder
