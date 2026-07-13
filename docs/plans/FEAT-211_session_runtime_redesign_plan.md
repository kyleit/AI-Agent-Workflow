<!-- File path: docs/plans/FEAT-211_session_runtime_redesign_plan.md -->

---
feature_id: FEAT-211
feature_name: Session Runtime Redesign (Logical Agents, Worker Pool, Tool Executor)
status: reviewed
stage: planning
created_at: 2026-07-13
updated_at: 2026-07-13
previous_artifact: ../brainstorming/FEAT-211_session_runtime_redesign.md
next_artifact: ../designs/FEAT-211_session_runtime_redesign_blueprint.md
---

# FEAT-211: Session Runtime Redesign Execution Plan

## 1. Current State Analysis
- **Runtime v2 Architecture**: Hoạt động dựa trên hai daemon ngầm bắt buộc (`Resident Runtime Manager` và `Resident Orchestrator`) để duy trì trạng thái. Mọi Agent chuyên gia chạy như một tiến trình Python OS riêng biệt và giao tiếp qua file đĩa `.session.json` được khóa bởi `OSFileLock`.
- **Existing Dependencies**: Lệ thuộc nặng vào các cuộc gọi `subprocess.Popen` rải rác trong các core skills, module `session.py` và `state_sync.py` ghi đĩa đồng bộ.
- **Components Kept**:
  - Split-state files structure (giữ nguyên cấu trúc đĩa tĩnh `.agents/state/*.json` để tương thích ngược).
  - Task Graph DAG definition.
- **Components Deprecated / Replaced**:
  - `OSFileLock` -> Thay thế hoàn toàn bằng asyncio in-memory Lock cho Session Mode.
  - Heartbeat & Watchdog -> Loại bỏ khỏi Session Core, chỉ giữ trong Resident Service.
  - Direct subprocess spawning trong Agents/Skills -> Phải đi qua gateway của Tool Executor.
- **Migration Constraints**: Không được gây ra breaking changes đối với CLI và Visualizer hiện tại khi chạy ở chế độ tương thích ngược.

---

## 2. Target Architecture Phân Lớp
Kiến trúc mới được tổ chức phân lớp độc lập, trong đó daemon chỉ xuất hiện ở Layer 6:

```text
Layer 6: Optional Host Layer (Background Job Host / Resident Service Host)
    │
Layer 5: Persistence & Event Store (SQLite WAL event logging)
    │
Layer 4: Tool Executor (Process boundary gateway & runtime validator)
    │
Layer 3: Scheduler & Worker Pool (Async Task Queue & ThreadPool worker execution)
    │
Layer 2: Logical Agent Runtime (In-memory logical agents)
    │
Layer 1: Session Runtime Core (In-process execution core)
```

---

## 3. Dependency Order & Milestone
Các FEAT phụ thuộc tuần tự theo chiều dọc từ Layer 1 lên Layer 6:

### Feature Dependency Graph (Đồ thị phụ thuộc):
```text
FEAT-211 (Session Core) ──> FEAT-212 (State & Event Store)
                              │
                              ▼
                        FEAT-213 (Logical Agent) & FEAT-214 (Context Engine)
                              │
                              ▼
                        FEAT-215 (Scheduler & Pool) ──> FEAT-216 (Tool Executor)
                                                          │
                                                          ▼
                                                    FEAT-217 (Permission Boundary)
                                                          │
                                                          ▼
                                                    FEAT-218 & FEAT-219 (API & SDK v3)
                                                          │
                                                          ▼
                                                    FEAT-220 & FEAT-221 (CLI/UI Adapters)
                                                          │
                                                          ▼
                                                    FEAT-222 & FEAT-223 (Bg & Resident Hosts)
                                                          │
                                                          ▼
                                                    FEAT-224 (Certification Suite)
```
- **Sequential Work**: Xây dựng Core (211-212) -> Agents (213-214) -> Scheduler (215) -> Executor (216-217).
- **Parallelizable Work**: Triển khai `FEAT-218` (Runtime API) và `FEAT-219` (Runtime SDK) có thể chạy song song sau khi Tool Executor và Scheduler định hình.
- **Milestones**:
  - Milestone 1: Khởi động CLI in-process session thành công và ghi nhận nhật ký vào SQLite WAL.
  - Milestone 2: Thực thi logical agents in-memory và dọn dẹp PGID subprocesses thành công khi gặp timeout.
  - Milestone 3: Chạy pass 100% Certification Test Suite (FEAT-224).

---

## 4. Sprint Breakdown

### Sprint 1: Core Session & WAL (FEAT-211 & FEAT-212)
- **Objective**: Khởi tạo nhân Session Runtime Core in-process và Event Store ghi WAL.
- **Scope**: Phát triển `SessionRuntimeCore`, cấu hình state machine, tích hợp SQLite WAL database.
- **Deliverables**: Lớp `SessionRuntimeCore`, `session_journal.db` schema.
- **Risks**: Tranh chấp ghi file SQLite WAL khi nhiều CLI chạy đồng thời -> Khắc phục: Dùng WAL mode và busy timeout.
- **Validation**: Đóng mở session và replay thành công các sự kiện sau crash.
- **DoD**: Code review pass, 100% unit tests pass.

### Sprint 2: Logical Agents & Context (FEAT-213 & FEAT-214)
- **Objective**: Thiết lập Logical Agent runtime và In-memory Shared Context.
- **Scope**: Khai báo `BaseLogicalAgent`, `SHARED_CONTEXT_CACHE`, asyncio lock, CoW engine và merge patch logic.
- **Deliverables**: Lớp `BaseLogicalAgent`, `SharedContextEngine` module.
- **Dependencies**: Sprint 1.
- **Risks**: Race condition khi nhiều agents cùng merge delta -> Khắc phục: Khóa in-memory ghi nguyên tử.
- **DoD**: Khởi tạo 100 agents logic chiếm < 1MB RAM, merge patch thành công không bị đè dữ liệu.

### Sprint 3: Scheduler & Worker Pool (FEAT-215 & FEAT-216)
- **Objective**: Xây dựng Scheduler điều phối và Tool Executor subprocess gateway.
- **Scope**: Lập lịch DAG, asyncio worker pool (Semaphores), `ExternalExecutor` bọc `os.setsid()`.
- **Deliverables**: Lớp `LogicalScheduler`, `ExternalExecutor` module.
- **Dependencies**: Sprint 2.
- **Risks**: Rò rỉ child process khi CLI crash đột ngột -> Khắc phục: Sử dụng PGID group signal SIGKILL.
- **DoD**: Cancel task dọn dẹp sạch 100% PGID tree con cháu.

### Sprint 4: Permission & SDK Core (FEAT-217, FEAT-218 & FEAT-219)
- **Objective**: Phân quyền phân cấp và định nghĩa API/SDK v3.
- **Scope**: Triển khai ranh giới Permission (Global/Session/Agent/Tool), thiết lập WebSocket JSON-RPC server và Python SDK v3.
- **Deliverables**: Module `PermissionBoundary`, JSON-RPC schema, SDK library.
- **Dependencies**: Sprint 3.
- **Risks**: Runtime Validator chặn nhầm các library call hợp lệ -> Khắc phục: whitelist chính xác stacktrace.
- **DoD**: Validator chặn đứng Popen gọi trực tiếp từ Agent và ném `ForbiddenProcessSpawnError`.

### Sprint 5: Migration & Client Adapters (FEAT-220 & FEAT-221)
- **Objective**: Di chuyển Core Skills và Client CLI/UI.
- **Scope**: Refactor `initialize-workflow`, `brainstorming` và các skills khác sang SDK v3. Thiết lập Compatibility Bridge cho CLI cũ.
- **Deliverables**: Skill updates, `workflow_runtime_bridge.py`.
- **Dependencies**: Sprint 4.
- **Risks**: Visualizer cũ bị treo do không thấy daemon file status -> Khắc phục: Cung cấp bridge giả lập file status.
- **DoD**: Lệnh CLI cũ hoạt động trơn tru qua bridge.

### Sprint 6: Background & Resident Service Hosts (FEAT-222 & FEAT-223)
- **Objective**: Triển khai các dịch vụ nền tùy chọn (Optional hosts).
- **Scope**: Phát triển Ephemeral Background Host (Mode 2) và Resident Service Host daemon (Mode 3).
- **Deliverables**: `background_host.py`, `resident_service.py`.
- **Dependencies**: Sprint 5.
- **DoD**: Khởi chạy daemon thành công ở Mode 3, cô lập an toàn tài nguyên giữa các session A/B/C.

### Sprint 7: Certification Suite (FEAT-224)
- **Objective**: Kiểm thử tích hợp tự động và chứng nhận hệ thống.
- **Scope**: Xây dựng chaos tests, stress tests và lệnh chứng nhận `aiwf certify`.
- **Deliverables**: `aiwf_certify.py` script.
- **Dependencies**: Sprint 6.
- **DoD**: Pass 100% test cases của bộ chứng nhận.

---

## 5. Migration Strategy
- **Compatibility Layer**: Compatibility Bridge tự động phát hiện và chuyển tiếp các CLI arguments v1/v2 thành payload JSON-RPC WebSocket gửi tới active session.
- **SDK & Skills**: Cung cấp adapter bọc `run_tool` thay thế cho lệnh gọi subprocess trực tiếp. Các skill cũ tiếp tục đọc `context.json` do session sync định kỳ để không bị gián đoạn.
- **Visualizer**: Visualizer kết nối WebSocket tới local WebSocket Server để cập nhật live log thay vì quét file liên tục.

---

## 6. Testing Strategy
- **Không tự động chạy test khi lưu file** (disable auto-testing on save) để tiết kiệm token và CPU.
- **Testing Entrypoints**: Lệnh chạy kiểm thử chỉ được gọi tường minh thông qua:
  - `/test` hoặc `/debug` trên chat UI.
  - `/verify` hoặc `/release` khi hoàn thành các phase.
- **Unit Tests**: Kiểm tra in-memory locks, delta context merge, state machine transition.
- **Integration Tests**: Kiểm tra WebSocket IPC handshake, dọn dẹp PGID subprocess.
- **Stress & Soak Tests**: Chạy 500 agents logic trên pool size = 4 để kiểm tra backpressure. Giám sát rò rỉ RAM của resident daemon trong 24 giờ.
- **Certification Tests**: Chạy lệnh `aiwf certify` kiểm thử chaos inject (giả lập crash ngắt nguồn) để xác minh tính ổn định của SQLite WAL.

---

## 7. Risk Management
- **GIL event loop blocking**: Khắc phục bằng cách offload các tác vụ CPU nặng (AST parsing, hash calculation) sang ThreadPool riêng biệt.
- **Context Contamination (Xung đột ghi đè)**: Khắc phục bằng CoW (Copy-on-Write) và so sánh revision version trước khi merge.
- **Permission leakage**: Khắc phục bằng cách khóa chặt session context, cấm Agent kế thừa full quyền của workspace.
- **Tool process leak**: Khắc phục bằng cách gán PGID qua `os.setsid()` và gọi `os.killpg` cưỡng bức.

---

## 8. Rollback Strategy
- **Rollback từng FEAT**: Mỗi FEAT được triển khai trên các nhánh tính năng git cô lập. Nếu gặp lỗi nghiêm trọng, thực hiện revert commit hoặc checkout nhánh cũ.
- **Feature Flags**: Duy trì cờ `experimental_session_runtime` trong `project.config.json`. Nếu set thành `false`, hệ thống tự động quay lại nhân daemon cũ của v2.
- **Legacy Compatibility Mode**: Bridge tự động fallback về single-process CLI cũ nếu daemon websocket server cổng 8765 không hoạt động.

## Recommended Next Skill
/blueprint
