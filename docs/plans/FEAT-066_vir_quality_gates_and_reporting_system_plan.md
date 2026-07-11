<!-- File path: docs/plans/FEAT-066_vir_quality_gates_and_reporting_system_plan.md -->

---
feature_id: FEAT-066
feature_name: Visual Intelligence Runtime — Quality Gates & Reporting System
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-066_vir_quality_gates_and_reporting_system.md
next_artifact: ../designs/FEAT-066_vir_quality_gates_reporting_blueprint.md
---

# FEAT-066: Visual Intelligence Runtime — Quality Gates & Reporting System

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Process ConsensusRecord to produce Quality Gate Result | [x] |
| FR-02 | Phase 1 | Task 1.2 | Load project gate thresholds (visual, design, performance) | [x] |
| FR-03 | Phase 1 | Task 1.3 | Implement PASS condition validation checks logic | [x] |
| FR-04 | Phase 1 | Task 1.4 | Implement PARTIAL validation checks (SHOULD only issues) | [x] |
| FR-05 | Phase 1 | Task 1.5 | Implement FAIL validation checks (veto active, critical errors) | [x] |
| FR-06 | Phase 1 | Task 1.6 | Implement BLOCKED validation checks (pipeline timeout) | [x] |
| FR-07 | Phase 1 | Task 1.7 | Bind CI/CD exit code mapping parameters (0, 1, 2) | [x] |
| FR-08 | Phase 1 | Task 1.8 | Audit log all gate evaluation steps to structured log files | [x] |
| FR-09 | Phase 1 | Task 1.9 | Integrate human gate overrides input interceptor | [x] |
| FR-10 | Phase 1 | Task 1.10| Export reports in both MD and JSON formatted extensions | [x] |
| FR-11 | Phase 1 | Task 1.11| Assemble complete diagnostic results arrays in reports | [x] |
| FR-12 | Phase 1 | Task 1.12| Hyperlink findings to stored artifact folders relative paths | [x] |
| FR-13 | Phase 1 | Task 1.13| Configure output report naming format patterns paths | [x] |
| FR-15 | Phase 1 | Task 1.14| Extract executive summaries suited for dashboards | [x] |
| FR-17 | Phase 1 | Task 1.15| Expose domain-specific confidence breakdowns | [x] |
| FR-14 | Phase 2 | Task 2.1 | Implement non-blocking asynchronous report writing tasks | [x] |
| FR-16 | Phase 2 | Task 2.2 | Build chronological event timeline tables in Markdown | [x] |
| FR-18 | Phase 2 | Task 2.3 | Capture performance footprints (peak RAM, CPU) | [x] |
| FR-19 | Phase 2 | Task 2.4 | Generate HTML/SVG timeline charts inside Markdown reports | [x] |
| FR-20 | Phase 2 | Task 2.5 | Compile CI package as a standard zip archive payload | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai bộ phân tích dữ liệu ConsensusRecord và phân cấp kết quả.
- **Task 1.2**: [Coder] - Viết trình nạp cấu hình giới hạn chất lượng từ dự án.
- **Task 1.3**: [Verifier] - Triển khai biểu thức logic xác định trạng thái PASS.
- **Task 1.4**: [Verifier] - Triển khai biểu thức logic xác định trạng thái PARTIAL.
- **Task 1.5**: [Verifier] - Triển khai biểu thức logic xác định trạng thái FAIL.
- **Task 1.6**: [Verifier] - Triển khai biểu thức logic xác định trạng thái BLOCKED.
- **Task 1.7**: [Coder] - Thiết lập gán mã thoát tương ứng (exit 0/1/2) cho CLI.
- **Task 1.8**: [Coder] - Tạo tệp tin audit ghi nhận các bước kiểm định chất lượng.
- **Task 1.9**: [Runtime] - Tích hợp cổng chặn chờ phê duyệt gỡ lỗi hoặc ghi đè (override) của con người.
- **Task 1.10**: [Coder] - Viết các module kết xuất dữ liệu Markdown và JSON.
- **Task 1.11**: [Documentation] - Định nghĩa template báo cáo Markdown đầy đủ.
- **Task 1.12**: [Coder] - Viết hàm phân tích đường dẫn tương đối liên kết tệp tin ảnh chụp.
- **Task 1.13**: [Architect] - Định dạng tên tệp tin báo cáo dựa trên Feature ID và Timestamp.
- **Task 1.14**: [Documentation] - Rút trích 2-3 câu tổng quát đầu tệp làm Executive Summary.
- **Task 1.15**: [Coder] - Định dạng bảng so sánh độ tin cậy từng domain (visual, design).
- **Task 2.1**: [Coder] - Tách luồng ghi đĩa (reports write) sang tác vụ nền chạy bất đồng bộ.
- **Task 2.2**: [Coder] - Viết module vẽ bảng timeline lịch sử điều tra dạng Markdown.
- **Task 2.3**: [Coder] - Đo đạc hiệu năng tiêu tốn CPU/RAM của VIR thông qua psutil.
- **Task 2.4**: [Architect] - Thiết lập cấu trúc mã vẽ sơ đồ dạng SVG/HTML timeline charts.
- **Task 2.5**: [Coder] - Triển khai nén zip toàn bộ ảnh chụp và báo cáo phục vụ lưu trữ CI.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.3 -> Task 1.7 -> Task 1.10 -> Task 2.5
- **Parallel Tasks**: [Task 1.2, Task 1.8, Task 1.9], [Task 1.11, Task 1.12, Task 1.13, Task 1.14, Task 1.15], [Task 2.1, Task 2.2, Task 2.3, Task 2.4]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.3), Task 1.10 (blocks Task 2.5)
- **Independent Tasks**: Task 1.9, Task 2.3
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6, Task 1.7 (Quality Gate evaluation core)
  - **Group 2**: Task 1.8, Task 1.9 (Audit logging and override gates)
  - **Group 3**: Task 1.10, Task 1.11, Task 1.12, Task 1.13, Task 1.14, Task 1.15 (Report generation core templates)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5 (Async telemetry & dynamic artifacts packaging)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/quality/gate.py` | Create | Trình kiểm soát Quality Gate chính |
| Task 1.7 | `vir_runtime/quality/exit_codes.py` | Create | Quản lý mã thoát CLI cho CI/CD |
| Task 1.9 | `vir_runtime/quality/override.py` | Create | Quản lý ghi đè phê duyệt thủ công |
| Task 1.10| `vir_runtime/reporting/engine.py` | Create | Trình điều phối xuất bản báo cáo MD & JSON |
| Task 1.11| `.agents/visual-runtime/templates/report.md`| Create | Template mẫu cho báo cáo kết quả |
| Task 2.3 | `vir_runtime/reporting/telemetry.py` | Create | Đo lường RAM/CPU tiêu thụ |
| Task 2.5 | `vir_runtime/reporting/packager.py` | Create | Trình đóng gói zip artifacts |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của `QualityGateEvaluator` và `ReportPublisher`.
- **Provider Pattern details**: Mẫu bọc các bộ lọc template và nén zip, che giấu các thư viện ngoài.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận Consensus verdict -> chạy so khớp threshold -> tính mã thoát -> khởi chạy nền (async task) ghi MD/JSON -> thu thập dữ liệu ram/cpu -> vẽ biểu đồ SVG -> đóng gói zip -> thoát tiến trình.
- **Migration Strategy & Testing Architecture**: Viết test unit cho Quality Gate sử dụng các mock ConsensusRecords có kết quả khác nhau.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_gate_evaluation.py` (Mapped to Task 1.1): Đảm bảo PASS/FAIL/BLOCKED được phân loại chính xác dựa trên ConsensusRecord.
  - `tests/unit/test_ci_exit_codes.py` (Mapped to Task 1.7): Xác thực trả về exit code 1 khi phán quyết là FAIL, 2 khi phán quyết là BLOCKED.
  - `tests/unit/test_report_schema.py` (Mapped to Task 1.10): Đảm bảo báo cáo JSON Schema khớp định dạng chuẩn hóa.
- **Integration Tests**:
  - `tests/integration/test_async_packaging.py` (Mapped to Task 2.5): Thử chạy phiên điều tra, ghi dữ liệu, xuất file zip, mở giải nén và kiểm tra tính toàn vẹn của tệp tin.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Phân loại chính xác kết quả Quality Gate, trả về exit codes đúng quy chuẩn trong CI.
  - [ ] Báo cáo MD và JSON xuất ra đầy đủ, chính xác đường dẫn tương đối của ảnh chụp.
  - [ ] Lưu vết ghi đè (override logs) thành công khi con người phê duyệt ghi đè.
- **Phase 2 Exit Criteria**:
  - [ ] Đóng gói zip hoàn chỉnh toàn bộ báo cáo và ảnh chụp thành công.
  - [ ] Báo cáo ghi nhận đầy đủ chỉ số CPU/RAM cực đại (peak).

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Ghi tệp tin zip hoặc kết xuất SVG làm nghẽn tiến trình con và gây đứng đơ CI.
  - *Steps*: Tạm tắt xuất hoạt ảnh SVG và nén zip, chỉ ghi tệp tin MD và JSON thuần túy, revert code `packager.py`.
  - *Recovery*: Đảm bảo tiến trình CI/CD tiếp tục thoát và trả kết quả nhanh chóng.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.7 | Yes | No | Yes | No | Yes | No | No |
| Task 1.10| Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Task 2.3 | Yes | No | Yes | Yes | Yes | No | No |
| Task 2.5 | Yes | Yes | Yes | No | No | Yes | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-066_vir_quality_gates_reporting_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/reporting/packager.py
- **Phase 3 Artifacts**: docs/adr/ADR-017_reporting_packaging.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch Quality gate/Reporting tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm thiết kế template báo cáo và thu thập ram/cpu (Task 1.11, 2.3) chạy song song với lõi gate.
- **Expected token savings**: Tiết kiệm ~45% tokens nhờ chạy các kiểm thử kết xuất Markdown/JSON trên dữ liệu mock đĩa cứng, không cần chạy toàn bộ sensor.
- **Recommended execution strategy**: Hoàn thành sớm phần logic phân cấp exit codes (gate.py) trước khi tinh chỉnh mỹ thuật cho tệp SVG timeline.

---

## Recommended Next Skill
/blueprint
