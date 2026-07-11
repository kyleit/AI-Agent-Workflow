<!-- File path: docs/plans/FEAT-054_update_source_and_interactive_initialization_plan.md -->

---
feature_id: FEAT-054
feature_name: Build update-source and Interactive Project Initialization
status: reviewed
stage: planning
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../brainstorming/FEAT-054_update_source_and_interactive_initialization.md
next_artifact: ../designs/FEAT-054_update_source_and_interactive_initialization_blueprint.md
---

# FEAT-054: Build update-source and Interactive Project Initialization

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Lệnh `aiwf update-source` và các alias trong wrapper CLI | [x] |
| FR-02 | Phase 1 | Task 1.2 | Logic kiểm tra Git, fetch, hiển thị diff, ff-only pull | [x] |
| FR-03 | Phase 1 | Task 1.3 | Hỗ trợ các cờ `--check`, `--dry-run`, `--json`, `--yes` | [x] |
| FR-04 | Phase 2 | Task 2.1 | Lệnh `aiwf init` hỗ trợ các tham số dòng lệnh | [x] |
| FR-05 | Phase 2 | Task 2.2 | Trình wizard câu hỏi 18 phần lưu draft state atomic | [x] |
| FR-06 | Phase 2 | Task 2.3 | Tích hợp bộ khuyến nghị thông minh (Go/FastAPI/Svelte) | [x] |
| FR-07 | Phase 2 | Task 2.4 | Sinh các tệp cấu hình mẫu và PROJECT_PROFILE.md | [x] |

## 2. Task Ownership & Roles
- **Task 1.1**: [Coder] - Triển khai routing lệnh `update-source` trong `bootstrap.ps1`.
- **Task 1.2**: [Architect] - Thiết kế lớp `SourceRepositoryService` xử lý Git logic.
- **Task 1.3**: [Coder] - Thực thi các tham số `--check`, `--dry-run`, `--json` cho CI.
- **Task 2.1**: [Coder] - Định nghĩa subcommand `init` trong `workflow_runtime.py`.
- **Task 2.2**: [Architect] - Thiết kế cấu trúc `InitQuestionnaire` quản lý state wizard.
- **Task 2.3**: [Coder] - Tích hợp `RecommendationEngine` khuyến nghị stack.
- **Task 2.4**: [Coder] - Xây dựng `ScaffoldPlanner` và `TemplateRenderer`.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 ➔ Task 1.2 ➔ Task 2.1 ➔ Task 2.2 ➔ Task 2.4
- **Parallel Tasks**: [Task 1.3, Task 2.3]
- **Blocking Tasks**: Task 2.2 (blocks Task 2.4)
- **Independent Tasks**: Không có.
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2
  - Group 2: Task 2.1, Task 2.2, Task 2.3 (Parallel)
  - Group 3: Task 2.4

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation (Create/Modify/Delete/Do Not Modify) | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `bootstrap.ps1` | Modify | Thêm case routing cho `update-source` và `init` |
| Task 1.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Tích hợp subcommands và gọi helper classes |
| Task 1.2 | `skills/workflow-runtime/scripts/update_source.py` | Create | Lớp `SourceRepositoryService` quản lý update |
| Task 2.2 | `skills/workflow-runtime/scripts/init_wizard.py` | Create | Lớp `InitQuestionnaire` và `ScaffoldPlanner` |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**:
  - `SourceRepositoryService`: Các phương thức `fetch()`, `get_status()`, `pull_ff()`.
  - `InitQuestionnaire`: Các phương thức `ask_section()`, `save_draft()`, `load_draft()`.
  - `ScaffoldPlanner`: Phương thức `generate_plan()`, `execute_transaction()`.
- **Provider Pattern details**: Hỗ trợ tích hợp cấu hình provider cho Obsidian/Qdrant.
- **Data Flow / Sequence Flow**: Chuyển tiếp luồng từ wrapper CLI sang Python Core Engine.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - `skills/workflow-runtime/tests/unit/test_update_source.py` (Mapped to Task 1.2)
  - `skills/workflow-runtime/tests/unit/test_init_wizard.py` (Mapped to Task 2.2)
- **Integration Tests**:
  - `skills/workflow-runtime/tests/integration/test_cli_init_integration.py` (Mapped to Task 2.4)

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] Lệnh `aiwf update-source` thực hiện ff-only an toàn và vượt qua 100% unit tests.
- **Phase 2 Exit Criteria**:
  - [ ] Lệnh `aiwf init` chạy tương tác, tạo đúng cấu trúc thư mục, tệp cấu hình và PROJECT_PROFILE.md.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi Git làm hỏng cây thư mục framework gốc.
  - Steps: `git checkout .` và `git clean -fd`.
- **Phase 2 Rollback**:
  - Trigger: Quá trình khởi tạo dự án mới thất bại giữa chừng.
  - Steps: Xóa staging files tạm thời, khôi phục thư mục về trạng thái trống ban đầu.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | No | No | Yes | No | No |
| Task 1.2 | Yes | Yes | Yes | No | Yes | Yes | No |
| Task 2.2 | Yes | Yes | Yes | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: `docs/designs/FEAT-054_update_source_and_interactive_initialization_blueprint.md`
- **Phase 2 Artifacts**: `docs/designs/FEAT-054_update_source_and_interactive_initialization_blueprint.json`

## 11. Token & Execution Optimization
- **Sequential execution cost**: Thấp nhờ module hóa logic Python.
- **Parallel execution opportunities**: Chạy song song unit tests và tích hợp tests.
- **Expected token savings**: Tiết kiệm 40% token qua việc kế thừa helper classes hiện có.

## Recommended Next Skill
/blueprint
