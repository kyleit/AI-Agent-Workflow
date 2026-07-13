<!-- File path: docs/designs/FEAT-211_session_runtime_redesign_blueprint.md -->

---
feature_id: FEAT-211
feature_name: Session Runtime Redesign (Logical Agents, Worker Pool, Tool Executor)
status: reviewed
stage: blueprint
created_at: 2026-07-13
updated_at: 2026-07-13
previous_artifact: ../plans/FEAT-211_session_runtime_redesign_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Session Runtime Redesign

## 1. Objective
- **Mục tiêu kỹ thuật**: Hợp nhất nhân thực thi của AIWF vào cấu trúc chạy theo phiên (Session Runtime) in-process, loại bỏ sự phụ thuộc bắt buộc vào Resident Daemon ở chế độ chạy thông thường.
- **Lý do thay đổi Runtime v2**:
  - Runtime v2 map mỗi Agent chuyên gia vào một OS process độc lập gây trễ khởi động lớn và tiêu tốn nhiều RAM.
  - Sử dụng daemon ngầm bắt buộc dẫn đến rò rỉ bộ nhớ, treo lock đĩa, và lỗi split-brain khi ngắt terminal đột ngột.
- **Ranh giới (Boundary) của FEAT-211**: Định hình nhân Session Core, State Machine và giao thức ghi WAL. Không bao gồm việc cấu trúc lại hoàn toàn các plugins của bên thứ ba.

---

## 2. Architecture Design

### 2.1 Component Diagram (Sơ đồ cấu phần)
```text
  Client CLI / IDE Extension (JSON-RPC WebSocket client)
            │
            ▼
┌────────────────────────────────────────────────────────┐
│               Session Runtime (In-Process)             │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │           Layer 1: Session Runtime Core        │   │
│   └───────────────────────┬────────────────────────┘   │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │           Layer 2: Logical Agent Runtime       │   │
│   └───────────────────────┬────────────────────────┘   │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │           Layer 3: Scheduler & Worker Pool     │   │
│   └───────────────────────┬────────────────────────┘   │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │           Layer 4: Tool Executor               │   │
│   └───────────────────────┬────────────────────────┘   │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │           Layer 5: Persistence & Event Store   │   │
│   └────────────────────────────────────────────────┘   │
└───────────────────────────┬────────────────────────────┘
                            │ (Layer 6: Optional Hosts)
                            ▼
          Background Host / Resident Service Host
```

### 2.2 Layer Responsibilities & Dependencies
- **Layer 1 (Session Runtime Core)**: Chịu trách nhiệm khởi tạo, lưu giữ cấu trúc phiên và giải phóng tài nguyên.
- **Layer 2 (Logical Agent Runtime)**: Quản lý không gian nhớ in-memory chứa metadata của agent và các delta context.
- **Layer 3 (Scheduler & Worker Pool)**: Lập lịch DAG và điều phối tasks trên event loop/thread workers.
- **Layer 4 (Tool Executor)**: Ranh giới độc quyền spawn subprocess. Tích hợp bộ **Runtime Validator** chặn đứng các Agent/Skill tự gọi `subprocess.Popen` trực tiếp.
- **Layer 5 (Persistence & Event Store)**: Ghi event log xuống SQLite WAL làm cơ sở khôi phục (recovery).
- **Layer 6 (Optional Host Layer)**: Cung cấp background host hoặc resident service (chỉ chứa daemon ở đây).

*Ràng buộc thép (Hard Constraints)*:
- Agent không được tự spawn process.
- Skill không được tự điều phối workflow ngoài Session Core.
- Không một component nào ngoài Tool Executor được gọi subprocess.

---

## 3. Session Runtime Core Blueprint

### 3.1 Session Object & Lifecycle
```python
class SessionRuntimeCore:
    session_id: str                   # UUIDv4
    workspace_path: str               # Luôn là "."
    permission_mode: str              # "sandbox" | "full_access"
    status: str                       # State machine status
    event_store: SQLiteEventStore     # Event log reference
```

### 3.2 State Machine Transitions
- **created** ──> **initializing** ──> **planning** ──> **ready**
- **ready** ──> **running** <──> **waiting_for_tool**
- **running** ──> **integrating** ──> **verifying** ──> **final_review** ──> **completed**
- Mọi trạng thái có thể chuyển ngay sang **failed** hoặc **cancelled** nếu nhận được tín hiệu abort.

### 3.3 Session APIs

#### `create_session(request_id: str, work_item: str, mode: str) -> str`
- **Input**: ID request, active work item, execution mode (logical).
- **Output**: UUIDv4 `session_id`.
- **Lifecycle**: Chuyển sang `initializing`.
- **Permission**: Khóa chặt sandbox quyền ban đầu.
- **Error**: Ném `SessionInitError` nếu workspace không hợp lệ.

#### `load_session(session_id: str) -> SessionObject`
- **Input**: `session_id`.
- **Output**: `SessionRuntimeCore` instance.
- **Lifecycle**: Đọc file trạng thái, chuyển sang `ready`.

#### `resume_session(session_id: str) -> SessionObject`
- **Input**: `session_id`.
- **Lifecycle**: Phát lại sự kiện từ SQLite WAL để dựng lại context in-memory.

#### `checkpoint(session_id: str) -> str`
- **Lifecycle**: Chụp snapshot context hiện tại, ghi đè JSON đĩa đồng bộ.

#### `close_session(session_id: str) -> bool`
- **Lifecycle**: Giải phóng toàn bộ pool, đóng file handles, chuyển sang `completed`.

#### `status_query(session_id: str) -> dict`
- **Output**: JSON chứa tiến độ task, CPU, RAM usage.

#### `event_stream(session_id: str) -> AsyncGenerator[dict]`
- **Output**: Luồng NDJSON events thời gian thực.

---

## 4. Logical Agent Runtime Blueprint
- **Logical Agent != Process**: Agent chỉ là lớp logic chạy in-memory thuộc Event Loop của Session.
- **State Machine**: `declared` ──> `ready` ──> `scheduled` ──> `executing` ──> `completed/failed`.
- **Agent Capability**: Khai báo danh sách capabilities (ví dụ: `[read_code, run_tests]`).
- **Context Delta**: Mọi biến đổi được Agent ghi nhận vào `delta` dict riêng biệt để tránh ghi đè trực tiếp lên Shared Context.
- **Permission Scope**: Kế thừa hẹp từ Task. Agent không được tự nâng quyền hoặc kế thừa full workspace access.
- **Cancellation & Retry**: Dùng `asyncio.Task.cancel()`. Agent kiểm tra `is_cancelled` định kỳ. Hỗ trợ retry với exponential backoff.

---

## 5. Shared Context Engine Blueprint
- **Shared Immutable Context**: Chứa goal, requirements, base file map nạp 1 lần vào RAM.
- **Copy-on-Write (CoW)**: Agent sao chép slice context cần sửa, thực hiện thay đổi trên delta.
- **Merge Strategy (Optimistic Concurrency Control)**: Trước khi merge delta, kiểm tra `revision` version của shared context. Nếu trùng khớp -> tiến hành merge; nếu bị lệch -> ném `StateConflictError` và chạy conflict resolution.
- **Conflict Resolution**: Đẩy task sang `blocked_interactive` để người dùng chọn phương án giải quyết (Keep Mine/Keep Theirs/Merge).
- **Token & Memory Optimization**: Caching system prompt prefix cho LLM; tự động tóm tắt (summarize) hoặc dọn sạch (evict) log chạy thử cũ của các task đã hoàn thành nếu dung lượng context vượt quá threshold.

---

## 6. Scheduler & Worker Pool Blueprint
- **DAG Scheduler**: Duyệt Task DAG, đưa task không còn dependency vào hàng đợi.
- **Queue Model**: Hàng đợi ưu tiên (Priority Queue) dựa trên độ ưu tiên task (Phase 1 trước Phase 2).
- **Worker Types**:
  - **Async Worker**: Thực thi in-process (async tasks) cho các tác vụ I/O bound.
  - **Thread Worker**: Bọc các sync blocking calls của Python (AST parse, file hash).
  - **Process isolation**: Chỉ khởi chạy process worker khi thực thi plugin không tin cậy.
- **Worker Reuse**: Trả worker về trạng thái `idle` và dọn sạch local context sau khi hoàn thành task.
- **Backpressure & Resource Limits**: Giới hạn `max_queued_tasks = 100`. Nếu CPU load > 90% hoặc RAM khả dụng < 10%, tạm hoãn phân bổ task.
- **Multi-session Fairness**: Dùng Fair Share Queue phân quota CPU/RAM đều giữa các session đang active.

---

## 7. Tool Executor Blueprint (Process Boundary)
- **Tool Registry**: Danh sách trắng (allowlist) các lệnh ngoài được phép chạy (pytest, git, compile).
- **Tool Request Contract**:
  ```yaml
  command: list[str]
  cwd: str
  timeout: float
  permission_scope: str
  ```
- **Process Lifecycle & PGID Cleanup**:
  - Khởi tạo tiến trình bằng: `subprocess.Popen(cmd, preexec_fn=os.setsid)` để tạo Process Group ID (PGID) mới.
  - Khi gặp timeout hoặc cancellation: Gọi `os.killpg(pgid, signal.SIGKILL)` để quét sạch 100% child process tree con cháu.
- **Output Streaming**: Sử dụng async non-blocking pipes đọc stdout/stderr từng dòng đẩy về Event Bus của Session.

---

## 8. Permission Boundary Blueprint
- **Hierarchy Model**:
  ```text
  Global Permission ──> Session Permission ──> Agent Permission ──> Tool Permission
  ```
- **Inheritance Rules**: Cấp dưới thừa kế hẹp từ cấp trên. Agent không được tự nâng quyền vượt quá Task write-scope.
- **Escalation Protection**: Chặn đứng việc chạy lệnh nâng quyền (chmod, sudo) trong Tool Executor.
- **Full_Access Isolation**: Việc thay đổi permission mode của Session A được cô lập hoàn toàn trong biến nhớ của session đó, không ghi đè cấu hình toàn cục lên file session dùng chung của workspace để tránh leakage.

---

## 9. Persistence & Event Store Blueprint
- **SQLite WAL Schema**:
  ```sql
  CREATE TABLE events (
      event_id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      timestamp TEXT NOT NULL,
      topic TEXT NOT NULL,
      payload TEXT NOT NULL
  );
  ```
- **Replay & Recovery**: Đọc tuần tự `events` từ SQLite theo thời gian thực để dựng lại trạng thái Task DAG khi resume sau sự cố IDE/CLI crash.

---

## 10. API & SDK Boundary
- **Runtime API v3**: Các gói tin JSON-RPC 2.0 giao tiếp qua WebSocket local port `8765`.
- **SDK v3**: Thư viện Python cung cấp API `dispatch_logical_agent` và `run_tool` bọc sẵn cơ chế gửi/nhận websocket.
- **Compatibility Bridge**: CLI bridge tự động hứng arguments v1/v2 và route sang websocket client gửi tới daemon.

---

## 11. Migration Blueprint
- **Daemon Migration**: Vô hiệu hóa tính năng tự động chạy `Resident Orchestrator` khi khởi động.
- **Skill Migration Steps**:
  1. Thay thế lệnh gọi `subprocess.run` trong core skills sang API `run_tool` của SDK v3.
  2. Cấu hình `SKILL.md` sử dụng `execution_mode: "logical"`.
- **Visualizer**: Visualizer tự động connect tới local socket port 8765 để lấy status và logs.
- **Rollback**: Set feature flag `experimental_session_runtime: false` để tự quay lại nhân daemon cũ của v2.

---

## 12. Testing Blueprint
- **Không tự động chạy test khi thay đổi file** để bảo toàn CPU/token.
- **Unit Tests**:
  - `skills/workflow-runtime/tests/unit/test_session_core.py` (Validate state machine)
  - `skills/workflow-runtime/tests/unit/test_context_engine.py` (Validate lock & CoW)
- **Integration Tests**:
  - `skills/workflow-runtime/tests/integration/test_external_executor.py` (Validate PGID kill tree)
  - `skills/workflow-runtime/tests/integration/test_cli_bridge.py` (Validate compatibility bridge)
- **Stress & Chaos Tests**:
  - Enqueue 500 agents trên pool size = 4.
  - Chaos test: kill ngang tiến trình daemon để kiểm tra khả năng phục hồi từ SQLite WAL.

---

## 13. Implementation Mapping

| Blueprint Component | Source Module | Skill Affected | Test Affected |
| :--- | :--- | :--- | :--- |
| **Session Core** | `session_core.py` | `initialize-workflow` | `test_session_core.py` |
| **Event Store** | `event_store.py` | `initialize-workflow` | `test_event_store.py` |
| **Logical Agent** | `logical_agent.py` | `blueprint-to-implementation` | `test_logical_agent.py` |
| **Context Engine** | `context_engine.py` | `plan-to-blueprint` | `test_context_engine.py` |
| **Tool Executor** | `external_executor.py` | `workflow-runtime` | `test_external_executor.py` |
| **API & SDK v3** | `runtime_sdk.py` | `workflow-runtime` | `test_cli_bridge.py` |
| **Resident Host** | `resident_service.py` | `workflow-runtime` | `test_resident_service.py` |
