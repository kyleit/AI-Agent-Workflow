<!-- File path: docs/designs/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_blueprint.md -->

---
feature_id: FEAT-050
feature_name: Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_plan.md
next_artifact: ../../skills/workflow-runtime/scripts/
---

# Technical Design Blueprint & Implementation Contract – Refactor AIWF Runtime State: Split State + Event-Sourced Aggregator

## 0. Baseline Context & References

- **Memory Baseline**: High confidence. Project memory confirms `.agents/state/` currently contains flat JSON files (`agents.json`, `approvals.json`, `breakdown.json`, `context.json`, `recovery.json`, `runtime.json`, `usage.json`, `workflow.json`). `.session.json` still used as primary session bus.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/session.py` (L1–221): Contains `load_session`, `save_session_atomic`, `SessionLock`, `migrate_session_schema`. Already imports `state_sync.aggregate_state` and `deconstruct_state`.
  - `skills/workflow-runtime/scripts/state_sync.py`: Contains `read_json_safe`, `write_json_atomic`, `aggregate_state`, `deconstruct_state`.
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (3223 lines): Main CLI entry point with argparse; imports from session, state_sync, checkpoint, validator.
  - `.agents/state/`: Flat files — agents.json, approvals.json, breakdown.json, context.json, recovery.json, runtime.json, usage.json, workflow.json.
  - `.agents/runtime/`: checkpoints.json, handoffs.json, workflow.lock.

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/state_path.py` | NEW | Resolver cho canonical state paths; `get_state_dir()`, `get_events_path()`, `get_dashboard_path()` | None | Low – new standalone module |
| `skills/workflow-runtime/scripts/atomic_writer.py` | NEW | Atomic JSON write qua tmp+rename; `write_json_atomic(path, data)` | `state_path.py` | Low – critical safety layer |
| `skills/workflow-runtime/scripts/event_logger.py` | NEW | Append sự kiện vào `events.jsonl`; `emit_event(event_type, payload)` | `atomic_writer.py`, `state_path.py` | Low – append-only, không ghi đè |
| `skills/workflow-runtime/scripts/event_reducer.py` | NEW | Xử lý sự kiện để cập nhật sub-state JSON | `event_logger.py`, `atomic_writer.py` | Medium – nhiều trường hợp sự kiện |
| `skills/workflow-runtime/scripts/state_aggregator.py` | NEW | Đọc toàn bộ canonical state, tính `suggested_next_skill`, xuất `dashboard.json` | `event_reducer.py`, `state_path.py` | Medium – logic tổng hợp phức tạp |
| `skills/workflow-runtime/scripts/session.py` | MODIFY | Thêm `write_legacy_snapshot()` – sinh `.session.json` deprecated từ `dashboard.json` | `state_aggregator.py` | Medium – thay đổi file gốc quan trọng |
| `skills/workflow-runtime/scripts/state_sync.py` | MODIFY | Cập nhật `aggregate_state()` để gọi `StateAggregator` mới thay vì logic nội tuyến | `state_aggregator.py` | Medium – breaking change nhỏ |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Thêm parser group `state` với sub-commands: `migrate`, `aggregate`, `validate`, `emit`, `doctor`, `snapshot`, `recover` | Tất cả modules mới | High – CLI entry point thay đổi |
| `extensions/visualizer/resources/webview.html` | MODIFY | Cập nhật fetch URL từ `.session.json` sang `dashboard.json`; thêm banner "Legacy Mode" khi chỉ có `.session.json` | None | Low – UI-only change |

---

## 2. Target Folder Structure

```text
skills/workflow-runtime/
├── scripts/
│   ├── state_path.py          [NEW] – Path resolver canonical state
│   ├── atomic_writer.py       [NEW] – Safe atomic JSON writer
│   ├── event_logger.py        [NEW] – Append-only event emitter
│   ├── event_reducer.py       [NEW] – Event → sub-state reducer
│   ├── state_aggregator.py    [NEW] – Aggregator → dashboard.json
│   ├── session.py             [MODIFY] – Thêm write_legacy_snapshot()
│   ├── state_sync.py          [MODIFY] – Dùng StateAggregator mới
│   └── workflow_runtime.py    [MODIFY] – Thêm `state` sub-commands
├── tests/
│   ├── test_atomic_writer.py  [NEW]
│   ├── test_event_logger.py   [NEW]
│   ├── test_event_reducer.py  [NEW]
│   └── test_state_aggregator.py [NEW]

.agents/
├── state/
│   ├── project/
│   │   └── profile.json       [NEW] – project id, name, version, language
│   ├── workflow/
│   │   └── workflow.json      [MIGRATE from flat] – current skill, checkpoint, next skill
│   ├── runtime/
│   │   └── runtime.json       [MIGRATE from flat] – session health, context stats
│   ├── context/
│   │   └── context.json       [MIGRATE from flat] – token usage, breakdown
│   ├── recovery/
│   │   └── recovery.json      [MIGRATE from flat] – last known good state
│   ├── events/
│   │   └── events.jsonl       [NEW] – append-only event log
│   └── dashboard.json         [NEW] – aggregated view (read-only output)
├── .session.json              [MODIFY] – deprecated snapshot, _deprecated: true
```

---

## 3. Complete Class & Module Design

### `state_path.py` — StatePath

- **Responsibilities**: Trả về đường dẫn tuyệt đối/tương đối tới mọi thành phần của canonical state, đảm bảo không có hard-coded paths trong codebase.
- **Public Methods**:
  - `get_state_root() -> str` — Trả về `.agents/state/` (hoặc `AIWF_STATE_ROOT` env var nếu set).
  - `get_subdir(name: str) -> str` — Trả về path tới sub-directory (`project/`, `workflow/`, `runtime/`, `context/`, `recovery/`, `events/`).
  - `get_events_path() -> str` — Path tới `events/events.jsonl`.
  - `get_dashboard_path() -> str` — Path tới `dashboard.json`.
  - `get_legacy_session_path() -> str` — Path tới `.agents/.session.json`.
  - `ensure_dirs() -> None` — Tạo tất cả thư mục con nếu chưa tồn tại.

### `atomic_writer.py` — AtomicWriter

- **Responsibilities**: Ghi JSON an toàn, tránh tệp hỏng nửa chừng khi tắt đột ngột.
- **Public Methods**:
  - `write_json_atomic(path: str, data: dict) -> None` — Ghi vào `path.tmp`, flush, fsync, rồi `os.replace(tmp, path)`.
  - `append_jsonl(path: str, record: dict) -> None` — Append một dòng JSON vào JSONL file. Dùng `fcntl.flock` (POSIX) hoặc `msvcrt.locking` (Windows) để tránh xung đột ghi đồng thời.
- **Internal Methods**:
  - `_safe_rename(src: str, dst: str) -> None` — Wrapper xử lý khác biệt giữa OS.

### `event_logger.py` — EventLogger

- **Responsibilities**: Emitter sự kiện append-only vào `events.jsonl`.
- **Public Methods**:
  - `emit(event_type: str, payload: dict, event_id: str | None = None) -> str` — Tạo record `{event_id, event_type, timestamp, payload}` và append vào `events.jsonl`. Trả về `event_id`.
  - `read_all() -> list[dict]` — Đọc toàn bộ events từ `events.jsonl` theo thứ tự.
  - `compact(keep_last_n: int = 500) -> None` — Xóa các events cũ, giữ lại `keep_last_n` event gần nhất.
- **Event Type Constants** (string literals):
  - `WORKFLOW_INITIALIZED`, `SKILL_STARTED`, `SKILL_COMPLETED`, `SKILL_FAILED`
  - `PHASE_STARTED`, `PHASE_COMPLETED`, `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`
  - `WORKER_SPAWNED`, `WORKER_COMPLETED`, `WORKER_ORPHANED`
  - `FILE_LOCK_ACQUIRED`, `FILE_LOCK_RELEASED`
  - `DEBUG_PASSED`, `VERIFY_PASSED`, `RELEASE_REQUESTED`, `RELEASE_BLOCKED`

### `event_reducer.py` — EventReducer

- **Responsibilities**: Xử lý các sự kiện để cập nhật sub-state JSON files trong canonical layout.
- **Public Methods**:
  - `apply(event: dict) -> None` — Dispatch sự kiện tới handler tương ứng, ghi kết quả vào sub-state.
  - `replay_all() -> None` — Đọc toàn bộ `events.jsonl` và replay lần lượt để rebuild state.
- **Internal Methods** (handlers, mỗi handler nhận `payload: dict`):
  - `_on_workflow_initialized(p)` → cập nhật `workflow/workflow.json`
  - `_on_skill_started(p)` → cập nhật `workflow/workflow.json` (current_skill, current_step)
  - `_on_skill_completed(p)` → cập nhật `workflow/workflow.json`, `runtime/runtime.json`
  - `_on_phase_started(p)` → cập nhật `runtime/runtime.json`
  - `_on_phase_completed(p)` → cập nhật `runtime/runtime.json`, cập nhật ledger nếu có
  - `_on_task_started(p)`, `_on_task_completed(p)`, `_on_task_failed(p)` → cập nhật `runtime/runtime.json`

### `state_aggregator.py` — StateAggregator

- **Responsibilities**: Đọc toàn bộ canonical split state, tính toán các trường phái sinh, xuất `dashboard.json` và optional `.session.json` snapshot.
- **Public Methods**:
  - `aggregate() -> dict` — Đọc toàn bộ sub-state JSON, tính `suggested_next_skill`, `release_allowed`, `debug_allowed`, `verify_allowed`, `release_block_reason`. Trả về dict đã tính.
  - `write_dashboard() -> None` — Gọi `aggregate()` và ghi kết quả ra `dashboard.json` atomic.
  - `write_legacy_snapshot() -> None` — Gọi `aggregate()` và ghi `.session.json` với `_deprecated: true`, `_generated: true`, `_source: dashboard.json`.
- **Aggregation Logic** (key rules):
  - Nếu bất kỳ phase còn `pending` hoặc `in_progress`: `suggested_next_skill = "blueprint-to-implementation"`, `release_allowed = false`.
  - Nếu tất cả phases `completed` nhưng chưa có debug PASS: `suggested_next_skill = "implementation-to-debug"`, `release_allowed = false`.
  - Nếu debug PASS nhưng chưa verify: `suggested_next_skill = "debug-to-verify"`, `release_allowed = false`.
  - Nếu verify PASS: `release_allowed = true`, `suggested_next_skill = "implementation-to-release"`.

---

## 4. Detailed Interface Contracts

### `emit(event_type: str, payload: dict, event_id: str | None = None) -> str`
- **Parameters**:
  - `event_type`: Phải là một trong các constants định nghĩa trong `EventLogger`. Raise `ValueError` nếu không hợp lệ.
  - `payload`: Dict tùy ý, không được chứa `None` ở top-level keys quan trọng.
  - `event_id`: Optional UUID string. Nếu không cung cấp, tự sinh bằng `uuid.uuid4()`.
- **Return**: `event_id` dạng string.
- **Exceptions**: `IOError` khi không thể ghi vào `events.jsonl`. `ValueError` khi `event_type` không hợp lệ.
- **Validation**: Reject event_id trùng lặp (kiểm tra lần cuối trong file trước khi append).

### `write_json_atomic(path: str, data: dict) -> None`
- **Parameters**: `path` phải là đường dẫn tương đối (không bắt đầu bằng `/`). Raise `SecurityError` nếu vi phạm.
- **Exceptions**: `IOError` khi ghi thất bại; tệp gốc không bị thay đổi trong trường hợp này.
- **Validation**: `data` phải là JSON-serializable. Raise `TypeError` nếu không.

### `aggregate() -> dict`
- **Return**: Dashboard dict gồm: `{current_skill, current_command, checkpoint, suggested_next_skill, release_allowed, debug_allowed, verify_allowed, release_block_reason, implementation_status, phase_status[], worker_count, lock_count, _generated_at, _source: "split_state"}`.
- **Exceptions**: Nếu bất kỳ sub-state file nào bị hỏng (invalid JSON), trả về partial state với `_health: "degraded"` thay vì crash.

---

## 5. Configuration Schema

- **Config Flag** (trong `.agents/memory.config.json` hoặc env var):
  ```json
  {
    "state": {
      "root": ".agents/state",
      "generate_legacy_session_json": true,
      "events_compact_threshold": 1000,
      "dashboard_auto_aggregate": true
    }
  }
  ```
- **Migration Rule**: Khi chạy `state migrate`, đọc flat `.agents/state/*.json` và di trú vào thư mục con tương ứng. File gốc được backup vào `.agents/state/backups/` trước khi xóa.

---

## 6. Database & Storage Design

- Không thay đổi SQLite schema. Module này chỉ thao tác JSON files.
- **Storage Estimate**: `events.jsonl` tăng ~200 bytes/event. Với 1000 events/ngày → ~200KB/ngày. Compact tự động tại ngưỡng 1000 events.

---

## 7. Cache Architecture

- Không áp dụng layer cache riêng. `StateAggregator.aggregate()` đọc trực tiếp từ disk mỗi lần gọi. Caller tự cache kết quả nếu cần.

---

## 8. Error Model

| Exception | Trigger | Recovery Strategy | Log Level |
| :--- | :--- | :--- | :--- |
| `StateWriteError(IOError)` | `write_json_atomic` thất bại | Giữ nguyên tệp gốc, log path + traceback | ERROR |
| `EventDeduplicateError(ValueError)` | `event_id` trùng lặp khi emit | Skip emit, log warning | WARNING |
| `StateCorruptError(ValueError)` | Sub-state file không parse được | Trả về `_health: "degraded"`, không crash | WARNING |
| `SecurityError(ValueError)` | Path tuyệt đối được truyền vào write | Raise ngay, không ghi | CRITICAL |
| `MigrationError(RuntimeError)` | Di trú thất bại | Dừng migration, không xóa file gốc | ERROR |

---

## 9. Skill Integration Contracts

### `initialize-workflow/SKILL.md`
- **Before Hook**: Gọi `python workflow_runtime.py state doctor` để phát hiện state corruption.
- **After Hook**: Gọi `python workflow_runtime.py state aggregate` để refresh dashboard.

### `software-development-workflow/SKILL.md`
- **Runtime Call**: Sau mỗi bước checkpoint, gọi `python workflow_runtime.py state emit --type SKILL_COMPLETED --payload '{"skill": "...", "checkpoint": N}'`.

---

## 10. CLI & Runtime Contracts

| Command | Parameters | Output | Exit Code |
| :--- | :--- | :--- | :--- |
| `state migrate` | `--dry-run` (optional) | JSON report: files migrated, backup paths | 0 success, 1 error |
| `state aggregate` | `--output dashboard\|session\|both` | Path to written file(s) | 0 success, 1 error |
| `state validate` | none | JSON: `{valid: bool, errors: []}` | 0 valid, 1 invalid |
| `state emit` | `--type EVENT_TYPE --payload '{...}'` | `{event_id: "..."}` | 0 success, 1 error |
| `state doctor` | none | JSON health report with remediation hints | 0 healthy, 1 issues found |
| `state snapshot` | `--label "desc"` | Backup path | 0 success |
| `state recover` | `--from-snapshot path` | Restored path | 0 success, 1 error |

---

## 11. Sequence Flows

### Normal Event Emission Flow
1. Skill calls `workflow_runtime.py state emit --type SKILL_STARTED --payload '{...}'`
2. `EventLogger.emit()` generates `event_id = uuid4()`
3. Appends `{event_id, event_type, timestamp, payload}` to `events.jsonl`
4. `EventReducer.apply(event)` routes to `_on_skill_started()` handler
5. Handler reads `workflow/workflow.json`, updates `current_skill`, writes back via `AtomicWriter`
6. `StateAggregator.write_dashboard()` is called if `dashboard_auto_aggregate = true`
7. `dashboard.json` is written atomically
8. Optional: `.session.json` snapshot written with `_deprecated: true`

### State Migration Flow
1. `workflow_runtime.py state migrate` invoked
2. Snapshot of `.agents/state/*.json` saved to `.agents/state/backups/YYYYMMDD_HHMMSS/`
3. Each flat file mapped to nested sub-directory (e.g., `workflow.json` → `workflow/workflow.json`)
4. New directory structure created via `StatePath.ensure_dirs()`
5. Files copied atomically
6. Migration report written to `.agents/state/recovery/state-migration-report.json`
7. `dashboard.json` generated
8. `.session.json` snapshot generated with `_deprecated: true`

### Degraded State Recovery Flow
1. `workflow_runtime.py state doctor` detects corrupted sub-state file
2. Reports exact file path and JSON parse error
3. Suggests `state recover --from-snapshot latest` as remediation
4. User runs recover; latest backup restored
5. `state aggregate` re-run

---

## 12. Security & Safety

- **Workspace Boundary**: `AtomicWriter.write_json_atomic()` rejects any path containing `..` or starting with `/`. Raise `SecurityError`.
- **Path Validation**: All paths validated relative to workspace root before any write.
- **Write Restrictions**: Forbidden to write outside `.agents/` directory.
- **Rollback Safety**: `state migrate` creates backup before any modification. If backup fails, migration aborts entirely.
- **JSONL Integrity**: Each line in `events.jsonl` must be valid JSON. `EventLogger.read_all()` skips invalid lines and logs a warning rather than crashing.

---

## 13. Complete Test Matrix

| Req ID | Test Type | Test File | Component | Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit | `test_atomic_writer.py` | `AtomicWriter` | `write_json_atomic` succeeds; tmp file removed; original intact on failure |
| FR-02 | Unit | `test_event_logger.py` | `EventLogger` | Events appended in order; duplicate event_id rejected; `read_all()` returns correct count |
| FR-03 | Unit | `test_event_reducer.py` | `EventReducer` | `SKILL_STARTED` updates `workflow/workflow.json.current_skill`; `TASK_FAILED` marks task failed |
| FR-04 | Unit | `test_state_aggregator.py` | `StateAggregator` | Incomplete phases → `suggested_next_skill = "blueprint-to-implementation"` |
| FR-05 | Integration | `test_state_migration.py` | CLI `state migrate` | Running twice produces identical output (idempotent); backup created |
| NFR-01 | Unit | `test_atomic_writer.py` | `AtomicWriter` | Mock IOError mid-write → original file unchanged |
| TC-01 | Integration | `test_state_cli.py` | `workflow_runtime.py state *` | All 7 sub-commands exit 0 on valid input; valid JSON output |

---

## 14. Requirement Traceability Matrix

- `FR-01` → Task 1.1 → `StatePath.ensure_dirs()` → `state_path.py` → `test_atomic_writer.py` → Verified → Released.
- `FR-02` → Task 1.2 → `EventLogger.emit()` → `event_logger.py` → `test_event_logger.py` → Verified → Released.
- `FR-03` → Task 1.3 → `EventReducer.apply()` → `event_reducer.py` → `test_event_reducer.py` → Verified → Released.
- `FR-04` → Task 2.1 → `StateAggregator.write_dashboard()` → `state_aggregator.py` → `test_state_aggregator.py` → Verified → Released.
- `FR-05` → Task 2.2 → `StateAggregator.write_legacy_snapshot()` → `session.py` → `test_state_migration.py` → Verified → Released.
- `NFR-01` → Task 1.1 → `AtomicWriter.write_json_atomic()` → `atomic_writer.py` → `test_atomic_writer.py` → Verified → Released.

---

## 15. File-Level Implementation Contracts

- **File**: `skills/workflow-runtime/scripts/state_path.py`
  - **Purpose**: Resolver path canonical — không chứa business logic.
  - **Owner**: Coder
  - **Inputs**: `AIWF_STATE_ROOT` env var (optional, default `.agents/state`).
  - **Outputs**: Absolute/relative path strings.
  - **Notes**: Không import bất kỳ module AIWF nào khác để tránh circular import.

- **File**: `skills/workflow-runtime/scripts/atomic_writer.py`
  - **Purpose**: Ghi file JSON an toàn. Dùng `os.replace()` cross-platform.
  - **Owner**: Coder
  - **Inputs**: `(path: str, data: dict)`.
  - **Outputs**: None (side-effect: file written).
  - **Notes**: Dùng `tempfile.NamedTemporaryFile(dir=parent_dir, delete=False)` để đảm bảo tmp và target cùng partition.

- **File**: `skills/workflow-runtime/scripts/event_logger.py`
  - **Purpose**: Append events an toàn. Mỗi line là JSON object độc lập.
  - **Owner**: Coder
  - **Inputs**: `event_type: str`, `payload: dict`.
  - **Outputs**: `event_id: str`.
  - **Notes**: Sử dụng `threading.Lock()` nếu có thể bị gọi từ nhiều thread.

- **File**: `skills/workflow-runtime/scripts/event_reducer.py`
  - **Purpose**: Pure function transformer: event → state update. Không có side-effects ngoài file write.
  - **Owner**: Coder
  - **Notes**: Mỗi handler phải idempotent — gọi 2 lần với cùng event phải ra kết quả giống nhau.

- **File**: `skills/workflow-runtime/scripts/state_aggregator.py`
  - **Purpose**: Read-heavy, write-light. Aggregator không emit events mới.
  - **Owner**: Coder
  - **Notes**: Fallback gracefully khi sub-state file missing (treat as empty dict). Không crash.

- **File**: `skills/workflow-runtime/scripts/session.py` (MODIFY)
  - **Purpose**: Thêm `write_legacy_snapshot(dashboard: dict) -> None`. Sinh `.session.json` từ dashboard.
  - **Owner**: Coder
  - **Notes**: Phải backward-compatible — không xóa bất kỳ field nào đang được dùng bởi Visualizer cũ.

- **File**: `skills/workflow-runtime/scripts/workflow_runtime.py` (MODIFY)
  - **Purpose**: Thêm argparse sub-parser `state` với 7 sub-commands.
  - **Owner**: Coder
  - **Notes**: Mỗi sub-command phải exit với code 0 (success) hoặc 1 (error). JSON output ra stdout. Errors ra stderr.
