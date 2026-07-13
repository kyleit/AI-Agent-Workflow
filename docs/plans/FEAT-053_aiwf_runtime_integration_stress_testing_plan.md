<!-- File path: docs/plans/FEAT-053_aiwf_runtime_integration_stress_testing_plan.md -->

---
feature_id: FEAT-053
feature_name: AIWF Runtime Integration and Stress Testing Suite
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-053_aiwf_runtime_integration_stress_testing.md
next_artifact: ../designs/FEAT-053_aiwf_runtime_integration_stress_testing_blueprint.md
---

# FEAT-053: AIWF Runtime Integration and Stress Testing Suite

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Test fixtures: legacy session, flat split, nested canonical state | [x] |
| FR-01 | Phase 1 | Task 1.2 | test_state_migration.py: di trú idempotent, không hỏng nguồn | [x] |
| FR-02 | Phase 1 | Task 1.3 | test_state_aggregator.py + test_event_reducer.py | [x] |
| FR-03 | Phase 2 | Task 2.1 | test_phase_release_gates.py: block/allow theo đúng điều kiện | [x] |
| FR-04 | Phase 2 | Task 2.2 | test_file_locks.py + test_worker_registry.py | [x] |
| FR-04 | Phase 2 | Task 2.3 | test_task_dag_execution.py + test_resume_recovery.py | [x] |
| FR-05 | Phase 3 | Task 3.1 | test_runtime_stress.py: 50+ mock blueprints | [x] |
| FR-06 | Phase 3 | Task 3.2 | Failure injection: JSON write interrupt, permission denied, patch conflict | [x] |
| NFR-01 | Phase 1 | Task 1.1 | Fixtures dùng tempfile.mkdtemp(), không đụng workspace thật | [x] |
| NFR-02 | Phase 2 | Task 2.1 | Fast tests < 30s, stress tests opt-in | [x] |

## 2. Task Ownership & Roles

- **Task 1.1** — [QA/Coder] — Tạo test fixtures: `fixtures/state/legacy_session/.agents/.session.json`, `fixtures/state/flat_split/.agents/state/*.json`, `fixtures/state/nested_split/.agents/state/`, `fixtures/blueprints/FEAT-999_multi_phase_blueprint.json` (5 phases, 15+ tasks), `fixtures/blueprints/FEAT-998_single_phase_legacy_blueprint.md`, `fixtures/blueprints/FEAT-997_broken_blueprint.json` (cycle, missing ref, invalid path).
- **Task 1.2** — [QA/Coder] — Viết `test_state_migration.py`: kiểm tra di trú từ legacy session và flat split state sang canonical nested layout, idempotency, invalid JSON handling.
- **Task 1.3** — [QA/Coder] — Viết `test_state_aggregator.py` và `test_event_reducer.py`: kiểm tra tính đơn trị aggregation, chuỗi sự kiện đúng thứ tự, replay events.
- **Task 2.1** — [QA/Coder] — Viết `test_phase_release_gates.py`: kiểm tra toàn bộ điều kiện chặn/cho phép release, debug, verify theo từng trạng thái Phase.
- **Task 2.2** — [QA/Coder] — Viết `test_file_locks.py` và `test_worker_registry.py`: kiểm tra lock acquire/release, stale detect, orphan detect, PID tracking.
- **Task 2.3** — [QA/Coder] — Viết `test_task_dag_execution.py` và `test_resume_recovery.py`: kiểm tra DAG sorting, cycle detect, resume từ trạng thái lưu, abort an toàn.
- **Task 2.4** — [QA/Coder] — Viết `test_visualizer_dashboard_state.py`: kiểm tra dashboard.json được đọc đúng, không cần `.session.json`, hiển thị đúng trạng thái release_allowed.
- **Task 3.1** — [QA/Coder] — Viết `test_runtime_stress.py`: tự động sinh 50+ mock blueprint ngẫu nhiên, chạy từng luồng hoàn chỉnh (init → implement → debug → verify → release), xác nhận không có JSON hỏng, không có release sớm, không có active locks còn sót.
- **Task 3.2** — [QA/Coder] — Viết failure injection tests: giả lập lỗi ghi JSON dở dang (mock IOError), permission denied trên lock file, patch conflict. Xác nhận hệ thống không crash im lặng, luôn có recovery path.
- **Task 4.1** — [Documentation] — Viết `docs/guides/runtime-integration-testing.md` và `docs/guides/runtime-recovery-playbook.md`.

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 → [Task 1.2, Task 1.3] → [Task 2.1, Task 2.2, Task 2.3, Task 2.4] → [Task 3.1, Task 3.2] → Task 4.1
- **Parallel Tasks**: Task 1.2 và Task 1.3 (cùng fixtures); Task 2.1, 2.2, 2.3, 2.4 (test files độc lập); Task 3.1 và 3.2 (stress và failure riêng)
- **Blocking Tasks**: Task 1.1 chặn tất cả
- **Recommended Execution Groups**:
  - Group 1 (Sequential): Task 1.1
  - Group 2 (Parallel): [Task 1.2, Task 1.3]
  - Group 3 (Parallel): [Task 2.1, Task 2.2, Task 2.3, Task 2.4]
  - Group 4 (Parallel): [Task 3.1, Task 3.2]
  - Group 5 (Sequential): Task 4.1

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/` | Create (dir) | Thư mục fixtures |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/state/legacy_session/` | Create | Fixture legacy session |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/state/flat_split/` | Create | Fixture flat split state |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/state/nested_split/` | Create | Fixture nested canonical |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-999_multi_phase_blueprint.json` | Create | Blueprint fixture 5 phases |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-998_single_phase_legacy_blueprint.md` | Create | Blueprint legacy |
| Task 1.1 | `skills/workflow-runtime/tests/fixtures/blueprints/FEAT-997_broken_blueprint.json` | Create | Broken blueprint fixture |
| Task 1.2 | `skills/workflow-runtime/tests/test_state_migration.py` | Create | Test di trú state |
| Task 1.3 | `skills/workflow-runtime/tests/test_state_aggregator.py` | Create | Test aggregator |
| Task 1.3 | `skills/workflow-runtime/tests/test_event_reducer.py` | Create | Test reducer |
| Task 2.1 | `skills/workflow-runtime/tests/test_phase_release_gates.py` | Create | Test gates |
| Task 2.2 | `skills/workflow-runtime/tests/test_file_locks.py` | Create | Test locks |
| Task 2.2 | `skills/workflow-runtime/tests/test_worker_registry.py` | Create | Test workers |
| Task 2.3 | `skills/workflow-runtime/tests/test_task_dag_execution.py` | Create | Test DAG |
| Task 2.3 | `skills/workflow-runtime/tests/test_resume_recovery.py` | Create | Test resume/recovery |
| Task 2.4 | `skills/workflow-runtime/tests/test_visualizer_dashboard_state.py` | Create | Test dashboard |
| Task 3.1 | `skills/workflow-runtime/tests/test_runtime_stress.py` | Create | Stress test |
| Task 4.1 | `docs/guides/runtime-integration-testing.md` | Create | Hướng dẫn chạy test |
| Task 4.1 | `docs/guides/runtime-recovery-playbook.md` | Create | Playbook phục hồi |

## 5. Blueprint Preparation Inputs

- **Test Architecture**: Pytest-based, tất cả tests chạy trong `tempfile.mkdtemp()` workspaces
- **Key Test Patterns**: Arrange (tạo fixture state) → Act (gọi runtime function) → Assert (kiểm tra tệp kết quả và trạng thái)
- **Stress Test Strategy**: Generator sinh 50 blueprint ngẫu nhiên hợp lệ (không cycle), chạy từng cái với complete lifecycle, assert no corruption
- **Failure Injection**: Dùng `unittest.mock.patch` để giả lập lỗi tại điểm ghi file

## 6. Verification Strategy & Test Mapping

- **Fast Test Suite** (< 30s, chạy trong CI):
  - test_state_migration.py, test_state_aggregator.py, test_event_reducer.py, test_phase_release_gates.py, test_file_locks.py, test_worker_registry.py, test_task_dag_execution.py, test_resume_recovery.py, test_visualizer_dashboard_state.py
- **Stress Test Suite** (opt-in, local):
  - test_runtime_stress.py (50+ blueprints)
- **Failure Injection** (opt-in):
  - Phần `test_failure_injection` trong test_runtime_stress.py
- **Regression Suite**:
  - Toàn bộ test cũ trong `tests/test_runtime.py`

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Fixtures đầy đủ và hợp lệ (validated JSON).
  - [ ] test_state_migration.py vượt qua (idempotent, không hỏng nguồn).
  - [ ] test_state_aggregator.py và test_event_reducer.py vượt qua.
- **Phase 2 Exit Criteria**:
  - [ ] test_phase_release_gates.py vượt qua tất cả 8 test cases.
  - [ ] test_file_locks.py và test_worker_registry.py vượt qua.
  - [ ] test_task_dag_execution.py và test_resume_recovery.py vượt qua.
  - [ ] test_visualizer_dashboard_state.py vượt qua.
- **Phase 3 Exit Criteria**:
  - [ ] Stress test chạy thành công 50 mock blueprints không có JSON hỏng.
  - [ ] Failure injection tests xác nhận recovery path hoạt động.
  - [ ] Tài liệu playbook đầy đủ.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: Fixtures gây nhiễu test kết quả do dữ liệu sai.
  - Steps: Xóa toàn bộ `tests/fixtures/` và tạo lại.
- **Phase 3 Rollback**:
  - Trigger: Stress test làm chậm CI không chấp nhận được.
  - Steps: Chuyển stress tests sang opt-in flag `--stress`, loại khỏi default CI.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | No | No | No | No | No |
| Task 1.2 | Yes | No | No | No | No | No | No |
| Task 1.3 | Yes | No | No | No | No | No | No |
| Task 2.1 | Yes | No | No | No | No | No | No |
| Task 2.2 | Yes | No | No | No | No | No | No |
| Task 2.3 | Yes | No | No | No | No | No | No |
| Task 2.4 | Yes | No | No | Yes | No | No | No |
| Task 3.1 | Yes | No | No | No | No | No | No |
| Task 3.2 | Yes | No | No | No | No | No | No |
| Task 4.1 | No | No | No | No | Yes | No | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: Test fixture files, `docs/designs/FEAT-053_..._blueprint.md`
- **Phase 3 Artifacts**: `docs/guides/runtime-integration-testing.md`, `docs/guides/runtime-recovery-playbook.md`, `docs/adr/ADR-FEAT-053_runtime_state_aggregator_and_stress_testing.md`

## 11. Token & Execution Optimization

- **Sequential execution cost**: ~10 tasks × 600 tokens/task ≈ 6,000 tokens
- **Parallel execution opportunities**: Group 2 [Task 1.2+1.3] + Group 3 [Task 2.1+2.2+2.3+2.4] + Group 4 [Task 3.1+3.2] (~2,400 tokens saved)
- **Expected token savings**: ~40% nhờ parallelism rộng (test files hoàn toàn độc lập)
- **Recommended execution strategy**: Sequential cho Group 1 (fixtures là prerequisite); aggressive controlled parallel cho Group 2, 3, 4 vì tất cả test files không chồng write_set

## Recommended Next Skill
/blueprint
