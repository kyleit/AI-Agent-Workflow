<!-- File path: docs/plans/FEAT-052_safe_implementation_orchestrator_plan.md -->

---
feature_id: FEAT-052
feature_name: Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-052_safe_implementation_orchestrator.md
next_artifact: ../designs/FEAT-052_safe_implementation_orchestrator_blueprint.md
---

# FEAT-052: Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | DAG builder phân tích blueprint, phát hiện cycle | [x] |
| FR-02 | Phase 1 | Task 1.2 | File Lock Registry (`file-locks.json`) | [x] |
| FR-03 | Phase 1 | Task 1.3 | Worker Registry (`workers.json`) với PID tracking | [x] |
| FR-04 | Phase 2 | Task 2.1 | Orphan Check trước khi báo hoàn thành phase | [x] |
| FR-05 | Phase 2 | Task 2.2 | Patch-based parallel strategy: sinh `.patch`, apply tuần tự | [x] |
| NFR-01 | Phase 1 | Task 1.2 | Sequential fallback khi không xác định được write_set | [x] |
| TC-01 | Phase 1 | Task 1.2 | Khóa file dùng đường dẫn tương đối xuyên nền tảng | [x] |

## 2. Task Ownership & Roles

- **Task 1.1** — [Coder] — Viết `dag_planner.py`: phân tích JSON blueprint, sắp xếp Task theo Topological Sort, phát hiện cycle và tham chiếu Task không tồn tại. Xuất ra danh sách Execution Groups có thứ tự.
- **Task 1.2** — [Coder] — Viết `lock_manager.py`: quản lý `file-locks.json`. Hỗ trợ acquire (all-or-nothing), release, phát hiện stale lock (PID chết), reject path tuyệt đối và path traversal.
- **Task 1.3** — [Coder] — Viết `worker_manager.py`: quản lý `workers.json`. Ghi nhận PID khi spawn, cập nhật trạng thái (running, completed, failed, orphaned), giữ log file per-worker.
- **Task 2.1** — [Coder] — Viết `orchestrator.py`: controller chính điều phối DAG execution. Trước khi báo phase/feature complete, chạy Orphan Check. Hỗ trợ `implement abort` và `implement resume` thông qua `workflow_runtime.py`.
- **Task 2.2** — [Coder] — Viết `patch_applier.py`: tiếp nhận `.patch` file từ mỗi Task worker, kiểm tra patch chỉ động chạm đúng `write_set`, apply tuần tự vào workspace sau khi xác nhận không conflict.
- **Task 3.1** — [Coder] — Cập nhật `blueprint-to-implementation/SKILL.md`: thêm Safe Implementation Execution Policy (sequential default, parallel requires explicit conditions).
- **Task 3.2** — [Coder] — Cập nhật `workflow_runtime.py`: thêm sub-commands `implement abort`, `implement resume`, và Completion Gate checks bắt buộc.

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 → Task 1.2 → Task 1.3 → Task 2.1 → Task 2.2 → Task 3.1 → Task 3.2
- **Parallel Tasks**: Task 1.2 và Task 1.3 có thể chạy song song (khác nhau hoàn toàn về file)
- **Blocking Tasks**: Task 1.1 chặn mọi Task còn lại; Task 2.1 chặn Task 2.2
- **Recommended Execution Groups**:
  - Group 1 (Sequential): Task 1.1
  - Group 2 (Parallel): [Task 1.2, Task 1.3]
  - Group 3 (Sequential): Task 2.1 → Task 2.2
  - Group 4 (Parallel): [Task 3.1, Task 3.2]

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/dag_planner.py` | Create | DAG builder và topological sorter |
| Task 1.2 | `skills/workflow-runtime/scripts/lock_manager.py` | Create | File lock registry manager |
| Task 1.2 | `.agents/runtime/file-locks.json` | Create (schema) | Tệp trạng thái lock |
| Task 1.3 | `skills/workflow-runtime/scripts/worker_manager.py` | Create | Worker PID registry manager |
| Task 1.3 | `.agents/runtime/workers.json` | Create (schema) | Tệp registry tiến trình con |
| Task 2.1 | `skills/workflow-runtime/scripts/orchestrator.py` | Create | Controller điều phối DAG execution |
| Task 2.2 | `skills/workflow-runtime/scripts/patch_applier.py` | Create | Patch apply và xác nhận integrity |
| Task 2.2 | `.agents/runtime/patches/` | Create (dir) | Thư mục lưu patch file |
| Task 3.1 | `skills/blueprint-to-implementation/SKILL.md` | Modify | Thêm Safe Execution Policy |
| Task 3.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm implement abort, resume, completion gate |

## 5. Blueprint Preparation Inputs

- **Modules/Classes**: `DAGPlanner`, `LockManager`, `WorkerManager`, `SafeOrchestrator`, `PatchApplier`
- **Key Interfaces**: `dag_planner.build(blueprint_json)`, `lock_manager.acquire(task_id, write_set)`, `lock_manager.release(task_id)`, `worker_manager.register(pid, task_id)`, `orchestrator.run_phase(phase_id)`, `patch_applier.apply(task_id, patch_path)`
- **DAG Flow**: Blueprint JSON → DAG Build → Topological Sort → Group Assignment → Lock Acquire → Execute (sequential/controlled parallel) → Verify outputs → Lock Release → Orphan Check → Phase Complete
- **Parallel Safety Conditions**: Same dependency group + non-overlapping write_set + no global file touch + all locks acquired

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `test_dag_planner.py` → Task 1.1 (sort đúng, phát hiện cycle, phát hiện missing deps)
  - `test_file_locks.py` → Task 1.2 (acquire, release, stale detect, reject abs paths)
  - `test_worker_registry.py` → Task 1.3 (register, complete, orphan detect)
  - `test_patch_applier.py` → Task 2.2 (apply clean patch, reject conflicting patch)
- **Integration Tests**:
  - `test_task_dag_execution.py` → Task 2.1 (chạy fake tasks theo DAG với locks và workers)
  - Kiểm tra abort giữ nguyên log và không xóa source code
  - Kiểm tra resume không chạy lại completed tasks
- **Regression Tests**:
  - Toàn bộ workflow-runtime test cũ phải vượt qua

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] DAG builder phát hiện đúng cycle và dependency không hợp lệ.
  - [ ] Lock Manager ngăn Task B ghi file đang bị Task A khóa.
  - [ ] Worker Manager ghi nhận đúng PID và cập nhật trạng thái khi kết thúc.
- **Phase 2 Exit Criteria**:
  - [ ] Phase không thể hoàn thành khi còn worker đang chạy.
  - [ ] Patch applier từ chối patch chồng lên nhau.
  - [ ] `implement abort` thu hồi lock và không xóa source code.
  - [ ] `implement resume` tiếp tục từ Task queued đầu tiên sẵn sàng.
- **Phase 3 Exit Criteria**:
  - [ ] SKILL.md phản ánh đúng Safe Execution Policy.

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - Trigger: Lock Manager gây deadlock hoặc stale lock không tự giải phóng.
  - Steps: Xóa `file-locks.json`, khởi tạo lại trạng thái.
- **Phase 2 Rollback**:
  - Trigger: Patch applier gây hỏng source code.
  - Steps: Revert git commit, xóa `.agents/runtime/patches/`, khởi tạo lại từ Task đầu.

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | No | No | No | No |
| Task 2.2 | Yes | Yes | Yes | No | No | No | No |
| Task 3.1 | No | No | No | No | Yes | No | No |
| Task 3.2 | Yes | No | Yes | No | No | No | No |

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: `docs/designs/FEAT-052_safe_implementation_orchestrator_blueprint.md`, `docs/designs/FEAT-052_..._blueprint.json`
- **Phase 2 Artifacts**: `docs/adr/ADR-FEAT-052_safe_orchestrator_dag_locks_workers.md`
- **Phase 3 Artifacts**: `docs/guides/safe-implementation-execution.md`

## 11. Token & Execution Optimization

- **Sequential execution cost**: ~7 tasks × 900 tokens/task ≈ 6,300 tokens
- **Parallel execution opportunities**: Group 2 [Task 1.2, Task 1.3] + Group 4 [Task 3.1, Task 3.2] (~700 tokens saved)
- **Expected token savings**: ~11%
- **Recommended execution strategy**: Sequential cho Group 1 (DAG builder critical); controlled parallel cho Group 2 (lock_manager + worker_manager hoàn toàn độc lập) và Group 4 (SKILL.md docs)

## Recommended Next Skill
/blueprint
