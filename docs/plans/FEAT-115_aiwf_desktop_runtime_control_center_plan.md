<!-- File path: docs/plans/FEAT-115_aiwf_desktop_runtime_control_center_plan.md -->

---
feature_id: FEAT-115
feature_name: AIWF Desktop Runtime Control Center
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-115_aiwf_desktop_runtime_control_center.md
next_artifact: ../designs/FEAT-115_aiwf_desktop_runtime_control_center_blueprint.md
---

# FEAT-115: AIWF Desktop Runtime Control Center

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Project registry persistence structure & multi-project sidebar selection | [x] |
| NFR-03| Phase 1 | Task 1.2 | Auto-reconnecting WebSocket connection hub in Go backend | [x] |
| FR-02 | Phase 1 | Task 1.3 | Single Main Orchestrator lock verification engine | [x] |
| FR-03 | Phase 1 | Task 1.4 | Lifecycle action triggers (start/stop/restart/attach/detach) in Wails bindings | [x] |
| NFR-02| Phase 1 | Task 1.4 | Decoupled execution ensuring runtime survives UI exit | [x] |
| FR-05 | Phase 1 | Task 1.5 | SVG/Canvas DAG viewer inside frontend | [x] |
| FR-04 | Phase 2 | Task 2.1 | Hierarchical Live Subagents monitor panel | [x] |
| FR-06 | Phase 2 | Task 2.2 | Streamed log viewer with search & filter logic | [x] |
| FR-07 | Phase 2 | Task 2.3 | Live CPU/RAM charts & token budget usage tracker | [x] |
| FR-08 | Phase 3 | Task 3.1 | Desktop OS Notification dispatcher | [x] |

## 2. Task Ownership & Roles
- **Task 1.1**: [Coder] - Cấu hình Wails app boilerplate, định nghĩa tệp registry config và logic lưu trữ.
- **Task 1.2**: [Architect] - Thiết kế WebSocket hub đa luồng ở Go backend để gom connection pool của nhiều dự án.
- **Task 1.3**: [Architect] - Xây dựng cơ chế validate SQLite DB lock và runtime.lock file trước khi start/restart orchestrator.
- **Task 1.4**: [Coder] - Triển khai subprocess executor để trigger các lệnh daemon từ Go backend.
- **Task 1.5**: [Coder] - Triển khai Svelte view cho Dashboard và vẽ sơ đồ nodes/edges của Task Graph.
- **Task 2.1**: [Coder] - Lập trình cấu trúc cây hiển thị tiến trình Subagents.
- **Task 2.2**: [Coder] - Xây dựng log stream buffer ở UI để hiển thị log dòng chảy từ socket mà không làm gián đoạn render.
- **Task 2.3**: [Reviewer] - Thẩm định các phép tính toán tài nguyên phần cứng (RAM/CPU) từ backend Go để tránh overhead.
- **Task 3.1**: [Coder] - Tích hợp thư viện notification cross-platform ở backend Go.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.4 -> Task 1.5
- **Parallel Tasks**: [Task 2.1, Task 2.2, Task 2.3]
- **Blocking Tasks**: Task 1.4 blocks Task 1.5 (Must have backend API bindings ready before UI binding integration)
- **Independent Tasks**: Task 3.1 (Desktop notifications)
- **Recommended Execution Groups**:
  - Group 1: Setup & Registry (Task 1.1)
  - Group 2: Core Connection Hub & Locks (Task 1.2, Task 1.3)
  - Group 3: Process Execution Control (Task 1.4, Task 1.5)
  - Group 4: Live Observability (Task 2.1, Task 2.2, Task 2.3 in parallel)
  - Group 5: Notifications (Task 3.1)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `desktop/main.go` | Create | Thiết lập điểm khởi chạy Wails desktop |
| Task 1.1 | `desktop/registry.go` | Create | Định nghĩa logic lưu và load danh sách project |
| Task 1.2 | `desktop/supervisor.go` | Create | Khởi tạo WebSocket client pool kết nối các runtime ports |
| Task 1.3 | `desktop/lock_checker.go` | Create | Kiểm tra db/lease lock an toàn trước khi chạy |
| Task 1.4 | `desktop/executor.go` | Create | Exec commands ngầm bằng Go (start/stop/restart python runtime) |
| Task 1.5 | `desktop/frontend/src/Dashboard.svelte` | Create | Thiết kế Dashboard và bảng điều khiển trung tâm |
| Task 1.5 | `desktop/frontend/src/components/DAGViewer.svelte` | Create | Giao diện vẽ đồ thị Task DAG |
| Task 2.1 | `desktop/frontend/src/components/AgentMonitor.svelte` | Create | Panel hiển thị Subagent |
| Task 2.2 | `desktop/frontend/src/components/LogStreamer.svelte` | Create | Stream và filter logs |
| Task 2.3 | `desktop/frontend/src/components/ResourceGovernor.svelte` | Create | Vẽ biểu đồ tài nguyên CPU/RAM |
| Task 3.1 | `desktop/notifier.go` | Create | Đóng gói thông báo đẩy ra HĐH |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**: Wails Bindings Bridge, WebSocket Pool Hub, Subprocess Execution Wrapper.
- **Provider Pattern details**: Client-only pattern connecting to target ports dynamically discovery by scanning state.
- **Data Flow / Sequence Flow**: Svelte UI -> Wails Go Bindings -> Shell subprocess / WS -> local python runtime servers.
- **Migration Strategy & Testing Architecture**: Mock Python local servers outputting random telemetry payloads during integration testing of the Go/Svelte client.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**:
  - Test Go registry config file parse/write. (Mapped to Task 1.1)
  - Test Wails bindings responses via Go testing suite. (Mapped to Task 1.4)
- **Integration Tests**:
  - Simulate local python daemon outputs and check Svelte UI state change. (Mapped to Task 1.5)
- **Compatibility / Regression Tests**:
  - Verify app behavior when Python runtime drops connection unexpectedly.

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] Wails app khởi động < 1 giây, giao diện hiển thị danh sách dự án đầy đủ.
  - [ ] Trình điều khiển Start/Stop hoạt động mượt mà, không xảy ra duplicate main orchestrator.
  - [ ] Sơ đồ DAG render đúng màu sắc ứng với trạng thái tác vụ.
- **Phase 2 Exit Criteria**:
  - [ ] Log stream không bị nghẽn khi đẩy 500 lines/sec.
  - [ ] RAM tiêu hao của ứng dụng Wails duy trì dưới 120MB.
- **Phase 3 Exit Criteria**:
  - [ ] Desktop notifications hiển thị đúng nội dung khi workflow kết thúc.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Wails app gặp crash liên tục khi khởi chạy trên hệ thống OS mục tiêu hoặc gây lỗi rò rỉ bộ nhớ nghiêm trọng.
  - Steps: Revert git commits liên quan đến desktop setup, quay lại sử dụng CLI / Visualizer extension làm UI dự phòng.
  - Recovery: Xác thực trạng thái của Python daemon để đảm bảo không bị ảnh hưởng do Wails crash.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | No | No | Yes | No | No |
| Task 1.2 | Yes | No | No | No | No | No | No |
| Task 1.3 | Yes | No | Yes | No | No | No | No |
| Task 1.4 | Yes | No | Yes | No | No | No | No |
| Task 1.5 | Yes | Yes | No | No | Yes | No | No |
| Task 2.1 | Yes | Yes | No | No | No | No | No |
| Task 2.2 | Yes | Yes | No | No | No | No | No |
| Task 2.3 | Yes | Yes | No | No | No | No | No |
| Task 3.1 | Yes | No | No | No | No | No | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-115_aiwf_desktop_runtime_control_center_blueprint.md
- **Phase 2 Artifacts**: docs/releases/Release_Notes_Control_Center.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: 0 extra token overhead during execution as Wails uses local IPC and socket interfaces.
- **Parallel execution opportunities**: Visual layouts and socket polling functions can be developed and validated concurrently.
- **Expected token savings**: Prevents duplicate orchestrator execution loops, saving up to 30% of unnecessary token cost.
- **Recommended execution strategy**: Group task milestones sequentially by phase priority to ensure base connectivity works first.

## Recommended Next Skill
/blueprint
