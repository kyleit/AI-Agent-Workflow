<!-- File path: docs/plans/FEAT-052_project_permissions_management_plan.md -->

---
feature_id: FEAT-052
feature_name: Project-Level Permission Initialization and Manual Permission Mode Management
status: reviewed
stage: planning
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: ../brainstorming/FEAT-052_project_permissions_management.md
next_artifact: ../designs/FEAT-052_project_permissions_management_blueprint.md
---

# FEAT-052: Project-Level Permission Initialization and Manual Permission Mode Management

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Cấu hình permissions.json và định dạng lưu trữ | [x] |
| FR-02 | Phase 1 | Task 1.1 | Hỗ trợ sandbox và full-access | [x] |
| FR-03 | Phase 1 | Task 1.2 | Các lệnh CLI quản lýpermissions (init, show, change, validate) | [x] |
| FR-04 | Phase 2 | Task 2.1 | Refactor `initialize-workflow` kiểm tra tĩnh | [x] |
| FR-05 | Phase 2 | Task 2.2 | Chặn ghi từ skills, bảo đảm read-only | [x] |

## 2. Task Ownership & Roles
- **Task 1.1 [Coder]**: Thiết kế JSON schema, cấu trúc `.agents/config/permissions.json` và cài đặt hàm đọc/ghi nguyên tử.
- **Task 1.2 [Coder]**: Tích hợp CLI namespace `permissions` và 4 câu lệnh con vào `workflow_runtime.py`.
- **Task 2.1 [Architect]**: Thiết lập ràng buộc và refactor `initialize-workflow` nạp tĩnh.
- **Task 2.2 [Reviewer]**: Kiểm tra tính read-only của cấu hình permissions trong tất cả skills.
- **Task 3.1 [Coder]**: Cài đặt migration logic từ session cũ sang JSON permissions mới.
- **Task 3.2 [Verifier]**: Cô lập thư mục cấu hình tạm trong quá trình chạy test suite.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 2.1 -> Task 2.2
- **Parallel Tasks**: [Task 3.1, Task 3.2]
- **Blocking Tasks**: Task 1.2 (blocks Task 2.1)
- **Independent Tasks**: Task 3.2
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2 (Sequential)
  - Group 2: Task 2.1, Task 2.2 (Sequential)
  - Group 3: Task 3.1, Task 3.2 (Parallel)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/session.py` | Modify | Nạp cấu hình tĩnh từ permissions.json |
| Task 1.1 | `skills/workflow-runtime/scripts/state_store.py` | Modify | Tích hợp lớp InMemoryStateStore cho test mode |
| Task 1.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Cài đặt parser và logic cho nhóm lệnh permissions |
| Task 2.1 | `skills/initialize-workflow/scripts/initialize_workflow.py` | Modify | Đọc tĩnh quyền, dừng khi chưa init |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**: Cung cấp PermissionsManager class trong python hỗ trợ validate, read, write.
- **Data Flow / Sequence Flow**: Luồng CLI commands -> atomic save -> session mirror.
- **Migration Strategy & Testing Architecture**: Cài đặt `AIWF_PERMISSION_CONFIG_ROOT` để chuyển hướng đường dẫn ghi file trong pytest.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - `skills/workflow-runtime/tests/test_permissions_cli.py` (Mapped to Task 1.2, Task 3.1)
  - `skills/workflow-runtime/tests/test_permissions_validation.py` (Mapped to Task 1.1)
- **Integration Tests**:
  - `skills/workflow-runtime/tests/test_permissions_init_workflow.py` (Mapped to Task 2.1)

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% lệnh CLI permissions hoạt động đúng đắn trên môi trường local.
  - [ ] permissions.json được tạo ra đúng vị trí và định dạng chuẩn.
- **Phase 2 Exit Criteria**:
  - [ ] `initialize-workflow` nạp tĩnh quyền thành công mà không hỏi lại.
  - [ ] Chặn đứng mọi hành vi tự ý sửa đổi quyền từ phía skills.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi cú pháp nghiêm trọng làm treo CLI runtime.
  - Steps: Revert git commit của `workflow_runtime.py` và xóa file permissions.json.
  - Recovery: Trả lại trạng thái ổn định của các subcommands khác.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | Yes | No |
| Task 1.2 | Yes | Yes | Yes | Yes | Yes | Yes | No |
| Task 2.1 | Yes | Yes | Yes | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-052_project_permissions_management_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-007_permissions_escalation_control.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Tiết kiệm 15% thời gian khởi tạo do không có prompts.
- **Expected token savings**: Tránh việc AI Agent suy luận lòng vòng khi đối mặt với prompt hỏi quyền lặp lại.

## Recommended Next Skill
/blueprint
