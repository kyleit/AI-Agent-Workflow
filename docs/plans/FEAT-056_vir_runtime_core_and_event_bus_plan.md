<!-- File path: docs/plans/FEAT-056_vir_runtime_core_and_event_bus_plan.md -->

---
feature_id: FEAT-056
feature_name: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md
next_artifact: ../designs/FEAT-056_vir_runtime_core_and_event_bus_blueprint.md
---

# FEAT-056: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Implement central asyncio Event Bus pub/sub topic dispatcher | [x] |
| FR-02 | Phase 1 | Task 1.2 | Create Orchestrator managing core lifecycle state machines | [x] |
| FR-03 | Phase 1 | Task 1.3 | Build runtime Agent Registry container | [x] |
| FR-04 | Phase 1 | Task 1.4 | Define validation rules for structural Agent Contracts | [x] |
| FR-05 | Phase 1 | Task 1.5 | Implement configuration parser loading profiles parameters | [x] |
| FR-06 | Phase 1 | Task 1.6 | Support dynamic subscription changes during profile switches | [x] |
| FR-07 | Phase 1 | Task 1.7 | Support priority routing sorting critical messages first | [x] |
| FR-08 | Phase 1 | Task 1.8 | Manage investigation context state carry-over structures | [x] |
| FR-09 | Phase 1 | Task 1.9 | Integrate stage timeout handler tasks | [x] |
| FR-11 | Phase 1 | Task 1.10| Enforce backpressure block limits on bounded queues | [x] |
| FR-12 | Phase 1 | Task 1.11| Build loop detector counting retries limits | [x] |
| FR-13 | Phase 1 | Task 1.12| Model structural Event Envelope fields with versions | [x] |
| FR-14 | Phase 1 | Task 1.13| Enforce at-least-once delivery, idempotency cache, and DLQ routing | [x] |
| FR-15 | Phase 1 | Task 1.14| Validate schema structures during event transmission | [x] |
| FR-16 | Phase 1 | Task 1.15| Apply configuration precedence logic layers | [x] |
| FR-17 | Phase 1 | Task 1.16| Expose local and project configuration parameters validation | [x] |
| FR-20 | Phase 1 | Task 1.17| Mask secret token strings in logs | [x] |
| FR-10 | Phase 2 | Task 2.1 | Emit heartbeat status messages over stdout channels | [x] |
| FR-18 | Phase 2 | Task 2.2 | Build structured logging and execution metrics formatters | [x] |
| FR-19 | Phase 2 | Task 2.3 | Assemble live traces mapping timeline lists | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai Event Bus sử dụng hàng đợi asyncio độc lập cho mỗi Topic.
- **Task 1.2**: [Architect] - Thiết lập sơ đồ máy trạng thái Orchestrator để quản lý vòng đời chạy.
- **Task 1.3**: [Coder] - Viết module Agent Registry quản lý nạp và gỡ cài đặt động.
- **Task 1.4**: [Verifier] - Triển khai xác thực cấu trúc hợp đồng Agent khi đăng ký.
- **Task 1.5**: [Coder] - Cài đặt nạp tệp tin cấu hình và phân tích tham số các profile.
- **Task 1.6**: [Coder] - Xử lý chuyển đổi đăng ký kênh nhận tin của các agent khi đổi profile chạy.
- **Task 1.7**: [Architect] - Thiết lập cấu trúc ưu tiên sắp xếp sự kiện (Priority Queue).
- **Task 1.8**: [Coder] - Thiết lập bộ nhớ đệm mang theo ngữ cảnh phiên điều tra (session state).
- **Task 1.9**: [Coder] - Tích hợp quản lý tiến trình bất đồng bộ kèm hủy bỏ task khi quá giờ (timeout).
- **Task 1.10**: [Architect] - Thiết kế cơ chế phản hồi ngược (backpressure) khi hàng đợi đạt giới hạn.
- **Task 1.11**: [Verifier] - Cài đặt bộ giám sát chống lặp vòng lặp vô hạn và thoát khẩn cấp.
- **Task 1.12**: [Architect] - Định nghĩa cấu trúc chuẩn hóa cho phong bì sự kiện (Event Envelope).
- **Task 1.13**: [Coder] - Viết logic lọc trùng sự kiện (idempotency) và định tuyến DLQ cho tin lỗi.
- **Task 1.14**: [Verifier] - Triển khai kiểm tra khớp cấu trúc JSON Schema cho payload sự kiện.
- **Task 1.15**: [Coder] - Viết bộ giải quyết mức độ ưu tiên nạp cấu hình (precedence resolution).
- **Task 1.16**: [Verifier] - Cài đặt trình kiểm tra hợp lệ cấu hình đầu vào của dự án.
- **Task 1.17**: [Coder] - Triển khai bộ lọc regex thay thế các chuỗi khóa bí mật thành `[REDACTED]`.
- **Task 2.1**: [Coder] - Bổ sung luồng phát tín hiệu nhịp tim (heartbeat JSON stream).
- **Task 2.2**: [Documentation] - Xây dựng tài liệu đặc tả các chỉ số đo lường hiệu năng cốt lõi.
- **Task 2.3**: [Coder] - Viết bộ thu thập và xâu chuỗi lịch sử sự kiện thành các đối tượng Timeline.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.12 -> Task 1.1 -> Task 1.13 -> Task 1.10
- **Parallel Tasks**: [Task 1.3, Task 1.4], [Task 1.5, Task 1.15, Task 1.16], [Task 1.8, Task 1.9, Task 1.11]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.3), Task 1.12 (blocks Task 1.14)
- **Independent Tasks**: Task 1.17, Task 2.1, Task 2.2, Task 2.3
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.12, Task 1.1, Task 1.13, Task 1.10 (Core Event Bus pipeline execution)
  - **Group 2**: Task 1.3, Task 1.4, Task 1.8 (Agent management & validation runtime)
  - **Group 3**: Task 1.5, Task 1.15, Task 1.16, Task 1.17 (Configuration and safety parameters parser)
  - **Group 4**: Task 1.2, Task 1.9, Task 1.11 (Orchestrator lifecycle & loop protection controls)
  - **Group 5**: Task 2.1, Task 2.2, Task 2.3 (Observability stream & metrics indicators setup)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/core/bus.py` | Create | Thiết lập Event Bus bất đồng bộ và hàng đợi Topic |
| Task 1.2 | `vir_runtime/core/orchestrator.py` | Modify | Tích hợp vòng đời chạy thực tế và timeout các pha |
| Task 1.3 | `vir_runtime/core/registry.py` | Create | Quản lý đăng ký động các agent trong hệ thống |
| Task 1.4 | `vir_runtime/domain/agent_contract.py` | Modify | Bổ sung các quy tắc xác thực phương thức và domain của agent |
| Task 1.5 | `vir_runtime/core/config.py` | Create | Đọc nạp tham số cấu hình hệ thống |
| Task 1.7 | `vir_runtime/core/priority_queue.py` | Create | Thiết lập hàng đợi ưu tiên cho các sự kiện khẩn cấp |
| Task 1.8 | `vir_runtime/domain/session_state.py` | Create | Quản lý bộ lưu trữ ngữ cảnh phiên chạy |
| Task 1.11| `vir_runtime/core/loop_protector.py` | Create | Giám sát và ngắt vòng lặp vô hạn của agent |
| Task 1.12| `vir_runtime/domain/event.py` | Create | Định nghĩa mô hình Event Envelope và cấu trúc Metadata |
| Task 1.13| `vir_runtime/core/idempotency.py` | Create | Bộ lọc loại bỏ trùng lặp sự kiện trùng ID |
| Task 1.17| `vir_runtime/utils/masking.py` | Create | Bộ lọc thay thế chuỗi nhạy cảm và secret token |
| Task 2.1 | `vir_runtime/core/heartbeat.py` | Create | Truyền phát trạng thái định kỳ dạng NDJSON |
| Task 2.3 | `vir_runtime/core/observability.py` | Create | Xâu chuỗi các dòng sự kiện thành Timeline phục vụ telemetry |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả API của `AsyncioEventBus(EventBus)` và `AgentRegistry`.
- **Provider Pattern details**: Interface cho phép nạp các adapter ghi nhận vết (logs, metrics) mà không phụ thuộc cụ thể vào framework ghi log bên ngoài.
- **Data Flow / Sequence Flow**: Vẽ luồng xử lý khi nhận tin từ bus, nạp vào hàng đợi của agent, kích hoạt bộ lọc idempotency, và đẩy vào hàm xử lý bất đồng bộ của agent.
- **Migration Strategy & Testing Architecture**: Chạy giả lập (mocking) toàn bộ các sensor phát tin để kiểm tra độ trễ định tuyến của bus dưới tải cao.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_event_bus.py` (Mapped to Task 1.1): Gửi 10,000 tin nhắn qua các topic; kiểm tra tính đúng đắn và tốc độ định tuyến (< 5ms).
  - `tests/unit/test_idempotency.py` (Mapped to Task 1.13): Đảm bảo gửi tin trùng ID chỉ được xử lý một lần duy nhất.
  - `tests/unit/test_loop_protector.py` (Mapped to Task 1.11): Giả lập agent chạy lặp; kiểm tra ngắt thành công sau đúng 3 lượt lặp.
  - `tests/unit/test_masking.py` (Mapped to Task 1.17): Đảm bảo các chuỗi API_KEY bị che thành công trước khi xuất ra log.
- **Integration Tests**:
  - `tests/integration/test_backpressure_isolated.py` (Mapped to Task 1.10): Đảm bảo agent VLM chậm không làm tắc nghẽn hàng đợi xử lý của DOM agent.
  - `tests/integration/test_priority_routing.py` (Mapped to Task 1.7): Kiểm tra các thông báo VETO được định tuyến xử lý trước các sự kiện thông tin thông thường.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các bài test hiệu năng định tuyến, cách ly backpressure, và lọc trùng vượt qua.
  - [ ] Hệ thống nạp cấu hình đúng thứ tự ưu tiên và kiểm tra hợp lệ thành công.
  - [ ] Bộ lọc secret masking bảo vệ thành công các API token thử nghiệm.
- **Phase 2 Exit Criteria**:
  - [ ] Trình thu thập log xuất ra luồng NDJSON hợp lệ theo thời gian thực.
  - [ ] Biểu đồ timeline sự kiện (Evidence/Investigation) được kết xuất chính xác dạng danh sách JSON.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Lỗi nghẽn luồng (deadlock) do Event Bus asyncio không giải phóng tài nguyên.
  - *Steps*: Revert các tệp tin trong `vir_runtime/core/`, khôi phục bản sao lưu của orchestrator.
  - *Recovery*: Trả về trạng thái lõi chạy đơn luồng tuần tự để cô lập lỗi.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 1.7 | Yes | Yes | Yes | No | No | No | No |
| Task 1.10| Yes | Yes | Yes | No | No | Yes | No |
| Task 1.12| Yes | Yes | No | No | No | No | No |
| Task 2.1 | Yes | No | Yes | Yes | Yes | No | No |
| Task 2.3 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - `docs/designs/FEAT-056_vir_runtime_core_and_event_bus_blueprint.md`
  - `docs/adr/ADR-006_asyncio_local_message_bus.md` (Already generated)
  - `docs/adr/ADR-007_queue_per_topic_routing.md` (Already generated)
- **Phase 2 Artifacts**:
  - `vir_runtime/core/observability.py`
  - `tests/performance/latency_report.json`

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích logic bus tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm phân tích cấu hình (Task 1.5, 1.15) có thể triển khai song song với nhóm logic hàng đợi (Task 1.1, 1.10, 1.13) để giảm thiểu thời gian chờ của Coder.
- **Expected token savings**: Tiết kiệm ~40% tokens bằng cách viết các bài test đơn vị độc lập cho bus mà không nạp toàn bộ runtime engines khác vào ngữ cảnh chạy thử.
- **Recommended execution strategy**: Tập trung hoàn thành lõi bus.py và test_event_bus.py trước khi phát triển các module cấu hình bổ trợ.

---

## Recommended Next Skill
/blueprint
