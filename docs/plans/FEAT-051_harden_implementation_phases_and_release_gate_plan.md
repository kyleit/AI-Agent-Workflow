<!-- File path: docs/plans/FEAT-051_harden_implementation_phases_and_release_gate_plan.md -->

---
feature_id: FEAT-051
feature_name: Harden AIWF Implementation Flow and Release Gate
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-051_harden_implementation_phases_and_release_gate.md
next_artifact: ../designs/FEAT-051_harden_implementation_phases_and_release_gate_blueprint.md
---

# FEAT-051: Harden AIWF Implementation Flow and Release Gate

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | `implementation-ledger.json` schema và read/write helpers | [x] |
| FR-02 | Phase 1 | Task 1.2 | Phase boundary logic: sau Phase N đề xuất Phase N+1 | [x] |
| FR-03 | Phase 1 | Task 1.3 | CLI resume: tìm Phase chưa hoàn thành tiếp theo | [x] |
| FR-04 | Phase 2 | Task 2.1 | Release Gate kiểm tra toàn diện trước khi release | [x] |
| FR-05 | Phase 2 | Task 2.2 | Luồng Partial Release với xác nhận người dùng rõ ràng | [x] |
| TC-01 | Phase 1 | Task 1.1 | Tương thích với blueprint cũ (coi tất cả task là 1 Phase) | [x] |

## 2. Task Ownership & Roles

- **Task 1.1** — [Coder] — Thiết kế schema và viết read/write helpers cho `implementation-ledger.json`. Hỗ trợ thêm trường `phases`, `current_phase`, `release_allowed`, `verify_allowed`, `debug_allowed`, `orphan_process_check`.
- **Task 1.2** — [Coder] — Viết Phase Boundary Controller trong `state_aggregator.py` (hoặc module độc lập `phase_controller.py`): kiểm tra sau khi một Phase hoàn thành, nếu còn Phase tiếp theo thì cập nhật `suggested_next_skill = blueprint-to-implementation` và `release_allowed = false`.
- **Task 1.3** — [Coder] — Thêm CLI command `implement resume` vào `workflow_runtime.py`: đọc ledger, tìm Phase đầu tiên có status `pending` hoặc `in_progress`, tiếp tục thực thi từ đó.
- **Task 2.1** — [Coder] — Viết `release_gate.py`: kiểm tra toàn diện ledger (all phases completed, no running workers, debug report PASS, verify report PASS) trước khi cho phép Release. In thông báo chặn rõ ràng.
- **Task 2.2** — [Coder] — Viết logic Partial Release: yêu cầu người dùng nhập cú pháp xác nhận rõ ràng, tạo release note đặc biệt ghi nhận đây là phát hành một phần.
- **Task 3.1** — [Coder] — Cập nhật Skill `implementation-to-release/SKILL.md` để tích hợp Release Gate bắt buộc trước mọi thao tác phát hành.
- **Task 3.2** — [Coder] — Cập nhật Skill `software-development-workflow/SKILL.md` để phản ánh luồng phase-aware mới: Phase N Done → Continue Phase N+1 (không nhảy sang Debug/Release).

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 → Task 1.2 → Task 1.3 → Task 2.1 → Task 2.2 → Task 3.1 → Task 3.2
- **Parallel Tasks**: Task 3.1 và Task 3.2 có thể chạy song song (các tệp khác nhau)
- **Blocking Tasks**: Task 1.1 chặn Task 1.2 và Task 1.3; Task 2.1 chặn Task 2.2
- **Recommended Execution Groups**:
  - Group 1 (Sequential): Task 1.1 → Task 1.2 → Task 1.3
  - Group 2 (Sequential): Task 2.1 → Task 2.2
  - Group 3 (Parallel): [Task 3.1, Task 3.2]

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `.agents/runtime/implementation-ledger.json` | Create (schema) | Sổ cái tiến trình thực thi Blueprint |
| Task 1.1 | `skills/workflow-runtime/scripts/ledger.py` | Create | Read/write helpers cho implementation ledger |
| Task 1.2 | `skills/workflow-runtime/scripts/phase_controller.py` | Create | Kiểm soát chuyển tiếp Phase và cập nhật đề xuất |
| Task 1.3 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm sub-command `implement resume` |
| Task 2.1 | `skills/workflow-runtime/scripts/release_gate.py` | Create | Kiểm tra toàn diện các điều kiện trước Release |
| Task 2.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm sub-command `implement partial-release` |
| Task 3.1 | `skills/implementation-to-release/SKILL.md` | Modify | Tích hợp Release Gate bắt buộc |
| Task 3.2 | `skills/software-development-workflow/SKILL.md` | Modify | Cập nhật luồng Phase-aware |

## 5. Blueprint Preparation Inputs

- **Modules/Classes**: `ImplementationLedger`, `PhaseController`, `ReleaseGate`, `PartialReleaseManager`
- **Key Interfaces**: `ledger.load()`, `ledger.save_atomic()`, `phase_controller.check_boundary()`, `release_gate.validate()`, `release_gate.partial_approve(confirmation_text)`
- **Data Flow**: Phase completes → PhaseController reads ledger → detects next Phase → sets aggregator state → Release Gate validates pre-conditions on release request
- **Phase Status Lifecycle**: `pending → in_progress → completed` (monotonic, no reversals)

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `test_ledger.py` → Task 1.1 (CRUD ledger, khởi tạo từ blueprint legacy)
  - `test_phase_controller.py` → Task 1.2 (kiểm tra đề xuất Phase N+1 sau khi Phase N done)
  - `test_release_gate.py` → Task 2.1 (kiểm tra gate chặn khi thiếu phases/debug/verify)
- **Integration Tests**:
  - Giả lập blueprint 3-phase, xác nhận mỗi phase chỉ đề xuất tiếp tục phase kế tiếp
  - Kiểm tra lệnh `implement resume` hoạt động đúng sau ngắt kết nối
- **Regression Tests**:
  - Blueprint 1-phase cũ vẫn hoạt động bình thường với Phase = Implementation Complete

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] `implementation-ledger.json` ghi nhận đúng trạng thái từng Phase và Task.
  - [ ] Sau Phase N hoàn thành, `suggested_next_skill` = blueprint-to-implementation (nếu còn Phase).
  - [ ] `implement resume` tiếp tục đúng từ Phase chưa hoàn thành.
- **Phase 2 Exit Criteria**:
  - [ ] `/release` bị chặn nếu bất kỳ Phase chưa hoàn thành, hoặc chưa có debug/verify PASS.
  - [ ] Partial Release yêu cầu nhập đúng cú pháp xác nhận.
  - [ ] Skill files được cập nhật đúng và phản ánh luồng mới.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: Ledger ghi sai trạng thái gây vòng lặp vô hạn hoặc mất Phase.
  - Steps: Xóa `implementation-ledger.json`, khởi tạo lại từ đầu.
  - Recovery: Chạy lại `implement resume` từ Phase 1.
- **Phase 2 Rollback**:
  - Trigger: Release Gate chặn quá nghiêm khắc, gây tắc nghẽn workflow.
  - Steps: Revert `release_gate.py` và skill files về bản trước.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | No | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | No | No | No | No |
| Task 2.2 | Yes | No | Yes | No | No | No | No |
| Task 3.1 | No | No | No | No | Yes | No | No |
| Task 3.2 | No | No | No | No | Yes | No | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: `docs/designs/FEAT-051_..._blueprint.md`, `docs/designs/FEAT-051_..._blueprint.json`
- **Phase 2 Artifacts**: `docs/adr/ADR-FEAT-051_release_gate_and_phase_control.md`

## 11. Token & Execution Optimization

- **Sequential execution cost**: ~7 tasks × 700 tokens/task ≈ 4,900 tokens
- **Parallel execution opportunities**: Task 3.1 + Task 3.2 (~300 tokens saved)
- **Expected token savings**: ~6%
- **Recommended execution strategy**: Sequential cho Group 1 và Group 2 (critical path logic); controlled parallel cho Group 3 (SKILL.md docs không xung đột write_set)

## Recommended Next Skill
/blueprint
