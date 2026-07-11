<!-- File path: docs/plans/FEAT-068_vir_execution_modes_plan.md -->

---
feature_id: FEAT-068
feature_name: Visual Intelligence Runtime — Runtime Execution Modes (CLI / IDE / CI / Daemon)
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-068_vir_runtime_execution_modes.md
next_artifact: ../designs/FEAT-068_vir_runtime_execution_modes_blueprint.md
---

# FEAT-068: Visual Intelligence Runtime — Runtime Execution Modes (CLI / IDE / CI / Daemon)

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Establish the Local CLI entry point parameter parser | [x] |
| FR-02 | Phase 1 | Task 1.2 | Design the CLI console logs formatters mapping stages | [x] |
| FR-03 | Phase 1 | Task 1.3 | Apply color coding (ANSI) options to CLI stdout outputs | [x] |
| FR-04 | Phase 1 | Task 1.4 | Produce the final CLI execution results summary table | [x] |
| FR-05 | Phase 1 | Task 1.5 | Connect profile variables parsing (`--profile` standard) | [x] |
| FR-06 | Phase 1 | Task 1.6 | Integrate headed/headless CLI parameters | [x] |
| FR-08 | Phase 1 | Task 1.7 | Bind the dynamic `--mode ide` selector | [x] |
| FR-09 | Phase 1 | Task 1.8 | Implement line-delimited JSON (ndjson) IPC outputs | [x] |
| FR-10 | Phase 1 | Task 1.9 | Format IPC properties mappings for IDE events | [x] |
| FR-14 | Phase 1 | Task 1.10| Bind the dynamic `--mode ci` selector | [x] |
| FR-15 | Phase 1 | Task 1.11| Minimum output parameters maps and exit codes for CI runs | [x] |
| FR-16 | Phase 1 | Task 1.12| Limit maximum CI session time boundaries defaults | [x] |
| FR-18 | Phase 1 | Task 1.13| Enforce non-interactive block paths on CI escalations | [x] |
| FR-19 | Phase 1 | Task 1.14| Format minimal diagnostic summaries suited for PR messages | [x] |
| FR-25 | Phase 1 | Task 1.15| Invoke VIR engine commands from thin client | [x] |
| FR-26 | Phase 1 | Task 1.16| Model arguments mappings (feature, blueprint, URL) for thin | [x] |
| FR-27 | Phase 1 | Task 1.17| Enforce LOC limits keeping thin client wrapper under 100 LOC | [x] |
| FR-07 | Phase 2 | Task 2.1 | Implement watcher loops `--watch` monitoring project changes | [x] |
| FR-11 | Phase 2 | Task 2.2 | Build IDE Extension visual state watch components (VS Code) | [x] |
| FR-12 | Phase 2 | Task 2.3 | Render inline annotations maps inside VS Code visualizers | [x] |
| FR-20 | Phase 2 | Task 2.4 | Implement `--mode daemon` background watch loops daemon | [x] |
| FR-21 | Phase 2 | Task 2.5 | Monitor DOM fingerprint changes periodically from background | [x] |
| FR-23 | Phase 2 | Task 2.6 | Build daemon stop scripts controllers | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai argparse phân tích cú pháp CLI của `vir_runtime`.
- **Task 1.2**: [Coder] - Thiết lập luồng in tiến trình nạp stage và evidence thời gian thực.
- **Task 1.3**: [Coder] - Viết helper tạo màu chữ ANSI trên terminal.
- **Task 1.4**: [Documentation] - Định dạng bảng kết quả tóm tắt cuối luồng.
- **Task 1.5**: [Coder] - Kết nối tham số nạp các profile tương ứng.
- **Task 1.6**: [Coder] - Đồng bộ hóa tham số headed/headless của Playwright.
- **Task 1.7**: [Architect] - Xây dựng cơ chế IPC truyền tin qua dòng luồng đầu ra stdout.
- **Task 1.8**: [Coder] - Thiết lập định dạng NDJSON (Newline Delimited JSON) cho luồng IDE.
- **Task 1.9**: [Architect] - Định dạng các thuộc tính tin nhắn giao tiếp IPC (stage_change, verdict_issued).
- **Task 1.10**: [Verifier] - Triển khai phát hiện tự động môi trường CI (không có TTY) để đổi mode.
- **Task 1.11**: [Coder] - Đồng bộ exit codes PASS(0)/FAIL(1)/BLOCKED(2)/PARTIAL(3) của Quality Gate.
- **Task 1.12**: [Verifier] - Cài đặt thời gian chạy tối đa (CI timeout decorator) mặc định 10 phút.
- **Task 1.13**: [Verifier] - Chặn tự động các luồng hỏi (prompt) tương tác khi chạy trong CI.
- **Task 1.14**: [Documentation] - Soạn thảo định dạng PR comment thô từ kết quả kiểm thử.
- **Task 1.15**: [Coder] - Chỉnh sửa skill `frontend-visual-debug` chuyển sang gọi lệnh của VIR.
- **Task 1.16**: [Coder] - Nạp tham số feature_id và URL từ kịch bản skill.
- **Task 1.17**: [Verifier] - Kiểm soát dòng mã (LOC check) của `frontend-visual-debug` mỏng dưới 100 LOC.
- **Task 2.1**: [Coder] - Viết vòng lặp theo dõi thay đổi thư mục (watch mode) của CLI.
- **Task 2.2**: [Coder] - Cập nhật giao diện extension VS Code nạp NDJSON hiển thị bảng điều tra.
- **Task 2.3**: [Coder] - Nhúng ảnh annotated inline vào các panel lỗi của IDE.
- **Task 2.4**: [Coder] - Khởi chạy daemon background sử dụng luồng chạy asyncio nền.
- **Task 2.5**: [Verifier] - Dùng DOM fingerprint băm làm cờ kích hoạt Lightweight audit khi thay đổi.
- **Task 2.6**: [Coder] - Viết lệnh dừng (stop daemon) hủy tiến trình daemon nền.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.7 -> Task 1.8 -> Task 1.15
- **Parallel Tasks**: [Task 1.3, Task 1.4, Task 1.5, Task 1.6], [Task 1.9, Task 1.10, Task 1.11, Task 1.12, Task 1.13, Task 1.14], [Task 1.16, Task 1.17], [Task 2.1, Task 2.4, Task 2.6], [Task 2.2, Task 2.3, Task 2.5]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.2), Task 1.7 (blocks Task 1.8), Task 2.4 (blocks Task 2.6)
- **Independent Tasks**: Task 1.17, Task 2.5
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6 (CLI parameters & interactive views)
  - **Group 2**: Task 1.7, Task 1.8, Task 1.9 (IDE integration and NDJSON IPC outputs)
  - **Group 3**: Task 1.10, Task 1.11, Task 1.12, Task 1.13, Task 1.14 (CI non-interactive execution modes)
  - **Group 4**: Task 1.15, Task 1.16, Task 1.17 (Thin client refactoring & LOC validation)
  - **Group 5**: Task 2.1, Task 2.4, Task 2.6 (Daemon background watchers and scheduling)
  - **Group 6**: Task 2.2, Task 2.3, Task 2.5 (VS Code extension updates & live visual annotation)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/core/cli.py` | Create | Trình phân tích argparse của CLI |
| Task 1.7 | `vir_runtime/core/ipc.py` | Create | Lớp truyền NDJSON sang IDE |
| Task 1.10| `vir_runtime/core/ci.py` | Create | Thiết lập mode CI không tương tác |
| Task 1.15| `.agents/skills/frontend-visual-debug/SKILL.md` | Modify | Tinh giản skill về mỏng gọi qua CLI |
| Task 2.4 | `vir_runtime/core/daemon.py` | Create | Quản lý tiến trình daemon nền |
| Task 2.2 | `extensions/visualizer/resources/webview.html` | Modify | Cập nhật giao diện hiển thị bảng điều tra |
| Task 2.2 | `extensions/visualizer/build.js` | Modify | Chạy node build biên dịch sang webviewHtml.ts |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả API của `CLIRunner`, `CIOrchestrator`, `IPCEmitter`, và `DaemonProcess`.
- **Provider Pattern details**: Định dạng luồng NDJSON JSON Schema phục vụ bắt tin bên phía Visualizer extension.
- **Data Flow / Sequence Flow**: Vẽ luồng khi CLI gọi -> nạp core -> chọn mode -> chạy pipeline -> gửi NDJSON qua stdout -> IDE đọc -> cập nhật giao diện -> gán exit code kết thúc.
- **Migration Strategy & Testing Architecture**: Viết các kịch bản test CLI nạp trực tiếp mock configs để xác nhận exit code và NDJSON in ra hợp lệ.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_cli_args.py` (Mapped to Task 1.1): Kiểm thử truyền các cờ `--mode ci` và `--profile lightweight` nhận cấu hình chuẩn.
  - `tests/unit/test_ipc_events.py` (Mapped to Task 1.8): Đảm bảo các dòng in NDJSON có cấu trúc đúng lược đồ JSON.
  - `tests/unit/test_thin_client_loc.py` (Mapped to Task 1.17): Xác thực logic tệp SKILL.md mỏng dưới 100 LOC.
- **Integration Tests**:
  - `tests/integration/test_ci_non_interactive.py` (Mapped to Task 1.13): Inject cuộc gọi cần hỏi quyền trong CI mode; đảm bảo chuyển sang BLOCKED thành công.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Khởi chạy VIR CLI thành công trong < 1.5 giây.
  - [ ] Exit codes phân tách chính xác cho các kịch bản lỗi trong môi trường CI.
  - [ ] Skill cũ được tinh gọn thành công về wrapper gọi lệnh mỏng (< 100 LOC).
- **Phase 2 Exit Criteria**:
  - [ ] Giao diện Visualizer extension (sau khi chạy build.js) hiển thị đúng bảng điều tra NDJSON.
  - [ ] Daemon chạy nền định kỳ quét thay đổi DOM fingerprint chính xác.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Giao diện NDJSON in ra làm tắc nghẽn luồng stdout của IDE khiến IDE Visualizer bị treo.
  - *Steps*: Tạm tắt xuất các NDJSON thừa, chỉ in ra stage transition và verdict, revert code `ipc.py`.
  - *Recovery*: Đảm bảo giao diện extension chạy mượt mà không treo thanh sidebar.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.7 | Yes | Yes | Yes | Yes | No | No | No |
| Task 1.10| Yes | Yes | Yes | No | Yes | Yes | Yes |
| Task 1.15| Yes | No | Yes | Yes | Yes | No | No |
| Task 2.2 | Yes | No | No | Yes | Yes | No | No |
| Task 2.4 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-068_vir_runtime_execution_modes_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/core/daemon.py
- **Phase 3 Artifacts**: docs/adr/ADR-020_ipc_ndjson.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch execution modes tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm viết CLI parser và nạp cấu hình CI chạy song song với lõi IPC.
- **Expected token savings**: Tiết kiệm ~40% tokens nhờ chạy các kiểm thử NDJSON trên đầu ra luồng mock (StringIO) không cần mở extension thực tế.
- **Recommended execution strategy**: Hoàn thành sớm phần argparse (cli.py) và NDJSON emitter (ipc.py) trước khi viết logic daemon chạy nền.

---

## Recommended Next Skill
/blueprint
