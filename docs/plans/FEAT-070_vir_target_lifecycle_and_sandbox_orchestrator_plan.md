<!-- File path: docs/plans/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator_plan.md -->

---
feature_id: FEAT-070
feature_name: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator.md
next_artifact: ../designs/FEAT-070_vir_target_lifecycle_and_sandbox_orchestrator_blueprint.md
---

# FEAT-070: Visual Intelligence Runtime — Target Lifecycle & Sandbox Orchestrator

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Implement auto-detection for target application platform stacks | [x] |
| FR-02 | Phase 1 | Task 1.2 | Prepare dynamic environment variables from script definitions | [x] |
| FR-03 | Phase 1 | Task 1.3 | Implement dynamic port scanner detecting unused ports | [x] |
| FR-04 | Phase 1 | Task 1.4 | Write subprocess tree tracker collecting all spawned child PIDs | [x] |
| FR-05 | Phase 1 | Task 1.5 | Create health check and TCP ready-state poller module | [x] |
| FR-06 | Phase 1 | Task 1.6 | Implement process group signals dispatcher with SIGKILL fallback | [x] |
| FR-07 | Phase 1 | Task 1.7 | Create temporary sandbox execution workspace directories | [x] |
| FR-08 | Phase 1 | Task 1.8 | Write database resetting and seeder execution runners | [x] |
| FR-11 | Phase 1 | Task 1.9 | Establish abstract Platform-Agnostic Sandbox interface protocols | [x] |
| FR-12 | Phase 1 | Task 1.10| Integrate command validation parsing safety policies | [x] |
| FR-09 | Phase 2 | Task 2.1 | Integrate browser session lifecycle state handlers | [x] |
| FR-10 | Phase 2 | Task 2.2 | Build crash monitor logs capturer and restart loops | [x] |
| FR-13 | Phase 2 | Task 2.3 | Define behavior override maps for local/CI/IDE/daemon run modes | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai bộ phân tích phát hiện công nghệ đích dựa trên tệp tin dự án.
- **Task 1.2**: [Coder] - Viết trình chuẩn bị biến môi trường (PORT, NODE_ENV) nạp cho tiến trình con.
- **Task 1.3**: [Coder] - Cài đặt bộ dò quét tìm cổng TCP rỗi.
- **Task 1.4**: [Architect] - Thiết lập cấu trúc lưu giữ PID và định danh Process Group (PGID).
- **Task 1.5**: [Coder] - Xây dựng bộ thăm dò sức khỏe endpoint HTTP/TCP có thời gian chờ (timeout).
- **Task 1.6**: [Coder] - Cài đặt truyền phát tín hiệu SIGTERM/SIGKILL cho toàn bộ cây tiến trình con.
- **Task 1.7**: [Coder] - Viết module khởi tạo thư mục tạm cô lập dữ liệu biên dịch.
- **Task 1.8**: [Verifier] - Thiết lập bộ copy sao lưu nhanh và reset dữ liệu SQLite giữa các lần chạy.
- **Task 1.9**: [Architect] - Thiết kế Protocol `SandboxAdapter` đa nền tảng (Web, Mobile, Containers).
- **Task 1.10**: [Verifier] - Triển khai bộ phân tích cú pháp chặn câu lệnh hủy hoại hệ thống (safety gate).
- **Task 2.1**: [Architect] - Thiết kế luồng phối hợp giữa đóng mở Browser và khởi chạy Sandbox.
- **Task 2.2**: [Coder] - Thiết lập luồng bắt sự kiện crash của tiến trình và kích hoạt tự phục hồi.
- **Task 2.3**: [Documentation] - Viết đặc tả quy trình chạy và xử lý tín hiệu thoát giữa các chế độ CI/IDE.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.9 -> Task 1.1 -> Task 1.4 -> Task 1.6
- **Parallel Tasks**: [Task 1.2, Task 1.3, Task 1.7], [Task 1.5, Task 1.8], [Task 2.2, Task 2.3]
- **Blocking Tasks**: Task 1.9 (blocks Task 1.1), Task 1.4 (blocks Task 1.6), Task 1.8 (blocks Task 2.1)
- **Independent Tasks**: Task 1.10, Task 2.1, Task 2.3
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.9, Task 1.1, Task 1.4, Task 1.6 (Process execution tree bootstrap engine)
  - **Group 2**: Task 1.2, Task 1.3, Task 1.7 (Environment configuration and network setups)
  - **Group 3**: Task 1.5, Task 1.8, Task 1.10 (Safety checker and health diagnostics)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3 (Failover crash monitors & documentation)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/sandbox/discovery.py` | Create | Phát hiện cấu hình dự án đích và cổng chạy |
| Task 1.2 | `vir_runtime/sandbox/env.py` | Create | Thiết lập và làm sạch biến môi trường |
| Task 1.3 | `vir_runtime/sandbox/ports.py` | Create | Dò quét tìm cổng trống |
| Task 1.4 | `vir_runtime/sandbox/tracker.py` | Create | Giám sát cây tiến trình con sử dụng psutil |
| Task 1.5 | `vir_runtime/sandbox/probe.py` | Create | Trình thăm dò readiness check |
| Task 1.6 | `vir_runtime/sandbox/killer.py` | Create | Cưỡng chế tắt cây tiến trình con |
| Task 1.7 | `vir_runtime/sandbox/workspace.py` | Create | Quản lý thư mục tạm và SQLite db copies |
| Task 1.9 | `vir_runtime/adapters/base/sandbox.py` | Create | Khai báo Protocol giao diện cho Sandbox |
| Task 1.10| `vir_runtime/sandbox/safety.py` | Create | Kiểm duyệt lệnh, chặn các lệnh destructive |
| Task 2.2 | `vir_runtime/sandbox/failover.py` | Create | Bắt sự kiện thoát tiến trình và khôi phục tự động |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của lớp `ProcessTracker` và `SandboxController`.
- **Provider Pattern details**: Định cấu hình adapter mặc định cho OS process, cho phép mở rộng các nhà cung cấp ảo hóa như Docker Compose hay Podman trong tương lai.
- **Data Flow / Sequence Flow**: Sơ đồ trình tự từ lúc nạp lệnh -> quét cổng -> chạy DB seeds -> khởi động server con -> thăm dò port HTTP -> phát tín hiệu ready cho Core.
- **Migration Strategy & Testing Architecture**: Chạy thử nghiệm bằng cách khởi tạo tiến trình Python http.server giả định và đo tốc độ tháo dỡ (kill) cây tiến trình.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_port_scanner.py` (Mapped to Task 1.3): Đảm bảo trả về đúng cổng rỗi trong khoảng tài nguyên cho phép.
  - `tests/unit/test_safety_gate.py` (Mapped to Task 1.10): Đảm bảo các lệnh nguy hại bị chặn đứng và ném ra lỗi bảo mật.
  - `tests/unit/test_process_killer.py` (Mapped to Task 1.6): Thử chạy tiến trình con tạo nhiều nhánh con (nested children), xác nhận dọn dẹp sạch 100% PIDs.
- **Integration Tests**:
  - `tests/integration/test_sandbox_bootstrap.py` (Mapped to Task 1.5): Thử nghiệm khởi động đầy đủ một server HTTP giả lập trong thư mục tạm, chạy thành công kịch bản seeds và kiểm tra cổng.
  - `tests/integration/test_crash_recovery.py` (Mapped to Task 2.2): Giả lập ngắt đột ngột tiến trình và kiểm tra bộ giám sát kích hoạt khởi động lại thành công.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% tiến trình con và cháu (process tree) được dọn dẹp sạch sẽ trong vòng 3 giây sau khi tắt.
  - [ ] Cấp phát cổng động hoạt động trơn tru không xảy ra xung đột.
  - [ ] Bộ lọc an toàn chặn đứng hoàn toàn các lệnh phá hoại thư mục ngoài.
- **Phase 2 Exit Criteria**:
  - [ ] Hệ thống phát hiện sự cố rơi (crash) và kích hoạt khôi phục tự động đúng số lần quy định.
  - [ ] Báo cáo logs tiến trình con được định tuyến chính xác về thư mục `.agents`.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Lỗi rò rỉ tiến trình con (zombie leak) chiếm hết cổng hoặc tài nguyên máy chủ kiểm thử.
  - *Steps*: Chạy lệnh dọn dẹp cưỡng chế của hệ điều hành, revert mã nguồn `vir_runtime/sandbox/`.
  - *Recovery*: Đảm bảo giải phóng toàn bộ cổng bị chiếm và khôi phục môi trường chạy sạch.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | No | Yes | No | No | No | No |
| Task 1.4 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.6 | Yes | Yes | Yes | No | No | No | No |
| Task 1.8 | Yes | No | Yes | No | Yes | Yes | Yes |
| Task 2.2 | Yes | Yes | Yes | Yes | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - `docs/designs/FEAT-070_vir_target_lifecycle_blueprint.md`
  - `docs/adr/ADR-009_subprocess_group_orchestration.md` (Already generated)
- **Phase 2 Artifacts**:
  - `vir_runtime/sandbox/failover.py`
  - `docs/guides/vir_sandbox_configuration.md`

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch quản lý tiến trình tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Tách biệt luồng quét cổng, thiết lập môi trường tạm (Task 1.2, 1.3, 1.7) chạy song song giúp tối ưu hóa thời gian phát triển.
- **Expected token savings**: Tiết kiệm ~35% tokens bằng cách tách biệt module thăm dò cổng và kiểm tra an toàn ra các test case nhỏ không cần khởi động trình duyệt.
- **Recommended execution strategy**: Hoàn thành phần thiết kế interface `SandboxAdapter` và bộ kill tiến trình trước để làm nền tảng kiểm thử tích hợp.

---

## Recommended Next Skill
/blueprint
