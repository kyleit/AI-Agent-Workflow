<!-- File path: docs/plans/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_plan.md -->

---
feature_id: FEAT-050
feature_name: Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator.md
next_artifact: ../designs/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_blueprint.md
---

# FEAT-050: Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Canonical nested state directory layout under `.agents/state/` | [x] |
| FR-02 | Phase 1 | Task 1.2 | Append-only event log `events.jsonl` writer | [x] |
| FR-03 | Phase 1 | Task 1.3 | Event reducer updating sub-state JSON files | [x] |
| FR-04 | Phase 2 | Task 2.1 | State Aggregator producing `dashboard.json` | [x] |
| FR-05 | Phase 2 | Task 2.2 | Backward-compatible `.session.json` deprecated snapshot | [x] |
| NFR-01 | Phase 1 | Task 1.1 | Atomic JSON write helper (tmp + rename) | [x] |
| NFR-02 | Phase 2 | Task 2.1 | Aggregation latency < 100ms | [x] |
| TC-01 | Phase 2 | Task 2.2 | Config flag `state.generate_legacy_session_json` | [x] |

## 2. Task Ownership & Roles

- **Task 1.1** — [Coder] — Tạo thư mục con chuẩn hóa `.agents/state/` (project/, workflow/, runtime/, context/, recovery/, events/). Viết `state_path.py` và `atomic_writer.py`.
- **Task 1.2** — [Coder] — Viết `event_logger.py`: hàm append sự kiện vào `events.jsonl` theo chuẩn JSONL, với trường `event_id`, `event_type`, `timestamp`, `payload`.
- **Task 1.3** — [Coder] — Viết `event_reducer.py`: xử lý danh sách sự kiện lõi (WorkflowInitialized, SkillStarted, SkillCompleted, PhaseStarted, PhaseCompleted, TaskStarted, TaskCompleted, TaskFailed) để cập nhật các tệp trạng thái con.
- **Task 2.1** — [Coder] — Viết `state_aggregator.py`: đọc toàn bộ split state, tính toán `suggested_next_skill`, `release_allowed`, `debug_allowed`, xuất `dashboard.json`.
- **Task 2.2** — [Coder] — Cập nhật `session.py` để tạo snapshot `.session.json` tương thích ngược với marker `_deprecated: true`, `_source: dashboard.json`.
- **Task 2.3** — [Coder] — Thêm các CLI sub-commands vào `workflow_runtime.py`: `state migrate`, `state aggregate`, `state validate`, `state emit`, `state doctor`, `state snapshot`, `state recover`.
- **Task 3.1** — [Coder] — Di trú các Skill hiện tại dừng ghi trực tiếp vào `.session.json`, thay bằng lệnh CLI `state emit`.
- **Task 3.2** — [Coder] — Cập nhật Visualizer Extension để ưu tiên đọc `dashboard.json` thay vì `.session.json`.

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 → Task 1.2 → Task 1.3 → Task 2.1 → Task 2.2 → Task 2.3 → Task 3.1 → Task 3.2
- **Parallel Tasks**: Task 2.2 và Task 2.3 có thể chạy song song sau Task 2.1
- **Blocking Tasks**: Task 1.1 chặn mọi Task còn lại
- **Recommended Execution Groups**:
  - Group 1 (Sequential): Task 1.1 → Task 1.2 → Task 1.3
  - Group 2 (Sequential): Task 2.1
  - Group 3 (Parallel): [Task 2.2, Task 2.3]
  - Group 4 (Sequential): Task 3.1 → Task 3.2

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/state_path.py` | Create | Resolver đường dẫn canonical cho state dirs |
| Task 1.1 | `skills/workflow-runtime/scripts/atomic_writer.py` | Create | Ghi file JSON an toàn qua tmp+rename |
| Task 1.2 | `skills/workflow-runtime/scripts/event_logger.py` | Create | Append sự kiện vào events.jsonl |
| Task 1.3 | `skills/workflow-runtime/scripts/event_reducer.py` | Create | Reducer xử lý sự kiện cập nhật sub-state |
| Task 2.1 | `skills/workflow-runtime/scripts/state_aggregator.py` | Create | Aggregator tổng hợp dashboard.json |
| Task 2.2 | `skills/workflow-runtime/scripts/session.py` | Modify | Xuất snapshot deprecated .session.json |
| Task 2.3 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm sub-commands `state *` |
| Task 3.1 | `skills/*/SKILL.md` (các skill ảnh hưởng) | Modify | Cập nhật lệnh ghi state sang `state emit` |
| Task 3.2 | `extensions/visualizer/resources/webview.html` | Modify | Đọc dashboard.json thay vì .session.json |

## 5. Blueprint Preparation Inputs

- **Modules/Classes**: `StatePath`, `AtomicWriter`, `EventLogger`, `EventReducer`, `StateAggregator`
- **Data Flow**: Event → append events.jsonl → Reducer → update sub-state JSON → Aggregator → dashboard.json + .session.json snapshot
- **Key Interfaces**: `emit_event(event_type, payload)`, `aggregate_state()`, `load_dashboard()`, `migrate_legacy_session()`
- **Migration Strategy**: Chạy `state migrate` một lần để di trú dữ liệu cũ; sau đó hệ thống tự duy trì canonical state.

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `test_atomic_writer.py` → Task 1.1 (kiểm tra ghi thành công và rollback khi lỗi)
  - `test_event_logger.py` → Task 1.2 (kiểm tra format JSONL, dedup event_id)
  - `test_event_reducer.py` → Task 1.3 (kiểm tra reducer trả về state đúng)
  - `test_state_aggregator.py` → Task 2.1 (kiểm tra dashboard.json chuẩn xác)
- **Integration Tests**:
  - `test_state_migration.py` → Task 2.2 (di trú từ legacy session và flat split state)
  - `test_state_cli.py` → Task 2.3 (xác thực output của từng CLI command)
- **Compatibility Tests**:
  - Kiểm tra Visualizer vẫn hiển thị đúng sau khi chuyển sang đọc `dashboard.json`

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Thư mục `.agents/state/` có đúng cấu trúc nested sau `state migrate`.
  - [ ] Sự kiện được append đúng vào `events.jsonl` sau mỗi thao tác.
  - [ ] Reducer cập nhật đúng tệp sub-state tương ứng.
  - [ ] 100% unit test Task 1.x vượt qua.
- **Phase 2 Exit Criteria**:
  - [ ] `dashboard.json` được tạo chính xác bởi Aggregator.
  - [ ] `.session.json` snapshot chứa `_deprecated: true`.
  - [ ] Tất cả CLI sub-commands `state *` hoạt động đúng.
  - [ ] Visualizer đọc `dashboard.json` thành công.
  - [ ] 100% integration test vượt qua.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: Lỗi nghiêm trọng khi di trú gây mất dữ liệu trạng thái.
  - Steps: Revert git commit; khôi phục `.session.json` từ snapshot cũ.
  - Recovery: Xác nhận hệ thống chạy lại với `.session.json` gốc.
- **Phase 2 Rollback**:
  - Trigger: Visualizer không hiển thị được dashboard.
  - Steps: Revert thay đổi trong webview.html; khôi phục đọc `.session.json`.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | No | No | No | No |
| Task 2.2 | Yes | Yes | Yes | No | No | No | No |
| Task 2.3 | Yes | No | Yes | No | No | No | No |
| Task 3.1 | Yes | No | No | No | Yes | No | No |
| Task 3.2 | Yes | No | No | Yes | No | No | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: `docs/designs/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_blueprint.md`, `docs/designs/FEAT-050_..._blueprint.json`
- **Phase 2 Artifacts**: `docs/adr/ADR-FEAT-050_split_state_event_sourcing.md`

## 11. Token & Execution Optimization

- **Sequential execution cost**: ~8 tasks × 800 tokens/task ≈ 6,400 tokens
- **Parallel execution opportunities**: Task 2.2 + Task 2.3 (~400 tokens saved)
- **Expected token savings**: ~6% với nhóm song song Group 3
- **Recommended execution strategy**: Sequential cho Phase 1 (critical path); controlled parallel cho Group 3 (Task 2.2 + 2.3 không chồng write_set)

## Recommended Next Skill
/blueprint
