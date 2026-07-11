<!-- File path: docs/plans/FEAT-057_vir_adapter_architecture_and_provider_contracts_plan.md -->

---
feature_id: FEAT-057
feature_name: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-057_vir_adapter_architecture_and_provider_contracts.md
next_artifact: ../designs/FEAT-057_vir_adapter_architecture_and_provider_contracts_blueprint.md
---

# FEAT-057: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Establish the abstract base contracts isolating all provider libraries | [x] |
| FR-02 | Phase 1 | Task 1.2 | Define the Protocol signature for Browser Adapter automation | [x] |
| FR-03 | Phase 1 | Task 1.3 | Define the Protocol signature for layered Vision Adapter | [x] |
| FR-04 | Phase 1 | Task 1.4 | Define the Protocol signature for framework State Adapter | [x] |
| FR-05 | Phase 1 | Task 1.5 | Define the Protocol signature for hybrid Storage Adapter | [x] |
| FR-06 | Phase 1 | Task 1.6 | Define the Protocol signature for agent Memory Adapter | [x] |
| FR-07 | Phase 1 | Task 1.7 | Create Adapter Registry managing n-type adapters lookup | [x] |
| FR-08 | Phase 1 | Task 1.8 | Enforce implicit validation mapping matching Protocol signatures | [x] |
| FR-09 | Phase 1 | Task 1.9 | Integrate adapters loading logic from config configurations | [x] |
| FR-10 | Phase 1 | Task 1.10| Model capability markers flags for active adapters | [x] |
| FR-11 | Phase 1 | Task 1.11| Implement graceful degradation when capabilities are missing | [x] |
| FR-12 | Phase 1 | Task 1.12| Establish headed and headless flag mappings for browsers | [x] |
| FR-17 | Phase 1 | Task 1.13| Expose python SDK API bindings structures | [x] |
| FR-13 | Phase 2 | Task 2.1 | Build dynamic plugins directory crawler loader | [x] |
| FR-14 | Phase 2 | Task 2.2 | Build dependency check constraints validator for external plugins | [x] |
| FR-15 | Phase 2 | Task 2.3 | Define compatibility limits and isolation layers parameters | [x] |
| FR-16 | Phase 2 | Task 2.4 | Implement lifecycle handlers (unload, health verification) for plugins | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Đặc tả ranh giới kiến trúc loại bỏ import thư viện ngoài trong core.
- **Task 1.2**: [Coder] - Triển khai Python Protocol cho Browser Adapter.
- **Task 1.3**: [Coder] - Triển khai Python Protocol cho Vision Adapter.
- **Task 1.4**: [Coder] - Triển khai Python Protocol cho State Adapter.
- **Task 1.5**: [Coder] - Triển khai Python Protocol cho Storage Adapter.
- **Task 1.6**: [Coder] - Triển khai Python Protocol cho Memory Adapter.
- **Task 1.7**: [Coder] - Viết module Adapter Registry kiểm soát đăng ký.
- **Task 1.8**: [Verifier] - Thiết lập kiểm tra duck typing của adapter khi khởi động.
- **Task 1.9**: [Coder] - Phân tích tệp tin `adapters.yaml` để nạp cấu hình tương ứng.
- **Task 1.10**: [Architect] - Thiết lập cấu trúc cờ đánh dấu tính năng (capability flags).
- **Task 1.11**: [Coder] - Viết logic tự động bỏ qua (degrade) các bước VLM/OCR nếu adapter báo thiếu.
- **Task 1.12**: [Coder] - Tích hợp cấu hình headed/headless cho Browser Playwright Adapter.
- **Task 1.13**: [Architect] - Thiết lập cấu trúc giao tiếp công khai của SDK (`vir_runtime`).
- **Task 2.1**: [Coder] - Triển khai bộ dò quét tệp tin (plugins crawler) nạp tệp `.py` động.
- **Task 2.2**: [Verifier] - Triển khai kiểm tra phụ thuộc thư viện của plugin khi nạp.
- **Task 2.3**: [Architect] - Xây dựng cơ chế phân cấp bảo mật và kiểm tra tương thích phiên bản của plugin.
- **Task 2.4**: [Coder] - Cài đặt cơ chế kiểm tra sức khỏe (health checks) và tháo nạp (unload) plugin nóng.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> [Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6] -> Task 1.7 -> Task 1.8
- **Parallel Tasks**: [Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6], [Task 1.9, Task 1.10, Task 1.12], [Task 2.1, Task 2.4]
- **Blocking Tasks**: Task 1.1 (blocks all Protocols), Task 1.7 (blocks Task 1.8), Task 2.1 (blocks Task 2.2)
- **Independent Tasks**: Task 1.13, Task 2.2, Task 2.3
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, [Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6] (Abstract Protocol interfaces design)
  - **Group 2**: Task 1.7, Task 1.8, Task 1.11 (Registry registration and verification flow)
  - **Group 3**: Task 1.9, Task 1.10, Task 1.12, Task 1.13 (Configuration loading and SDK initialization)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3, Task 2.4 (Plugin dynamic engine implementation)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/adapters/base/interface.py` | Create | Lớp cơ sở định nghĩa các adapter |
| Task 1.2 | `vir_runtime/adapters/base/browser.py` | Create | Protocol đặc tả giao thức Browser |
| Task 1.3 | `vir_runtime/adapters/base/vision.py` | Create | Protocol đặc tả giao thức Vision |
| Task 1.4 | `vir_runtime/adapters/base/state.py` | Create | Protocol đặc tả giao thức State |
| Task 1.5 | `vir_runtime/adapters/base/storage.py` | Create | Protocol đặc tả giao thức Storage |
| Task 1.6 | `vir_runtime/adapters/base/memory.py` | Create | Protocol đặc tả giao thức Memory |
| Task 1.7 | `vir_runtime/adapters/registry.py` | Create | Bộ quản lý đăng ký và kiểm tra adapter |
| Task 1.9 | `vir_runtime/adapters/config.py` | Create | Cài đặt nạp tệp cấu hình `adapters.yaml` |
| Task 1.13| `vir_runtime/__init__.py` | Create | Giao diện API công khai cho SDK bên ngoài |
| Task 2.1 | `vir_runtime/adapters/loader.py` | Create | Bộ nạp plugin động từ thư mục chỉ định |
| Task 2.3 | `vir_runtime/adapters/security.py` | Create | Giới hạn quyền và kiểm tra tương thích của plugin |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc các Protocol của `BrowserAdapter`, `VisionAdapter`, `StorageAdapter`.
- **Provider Pattern details**: Định cấu hình mẫu đăng ký adapter mặc định sử dụng Playwright, SQLite và Qdrant.
- **Data Flow / Sequence Flow**: Vẽ luồng khi runtime gọi AdapterRegistry nạp cấu hình, khởi tạo adapter, chạy hàm test-connection, báo cáo capability flags, và đưa trạng thái hoạt động về core.
- **Migration Strategy & Testing Architecture**: Cách thức chạy thử các test unit bằng cách tạo các lớp StubBrowserAdapter, StubVisionAdapter để không phụ thuộc vào tiến trình thực tế.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_protocols_typing.py` (Mapped to Task 1.8): Đảm bảo các lớp mock/stub adapter thỏa mãn duck typing của Protocol.
  - `tests/unit/test_adapters_config.py` (Mapped to Task 1.9): Đảm bảo nạp và phân tích cú pháp tệp tin `adapters.yaml` chính xác.
  - `tests/unit/test_degradation.py` (Mapped to Task 1.11): Đảm bảo hệ thống bỏ qua tầng VLM mượt mà nếu adapter không khai báo năng lực.
- **Integration Tests**:
  - `tests/integration/test_plugin_isolation.py` (Mapped to Task 2.3): Đảm bảo plugin thiếu tương thích hoặc bị lỗi không gây đổ vỡ core runtime.
  - `tests/integration/test_dynamic_loader.py` (Mapped to Task 2.1): Thử nạp động một tệp tin adapter ngoài và thực thi chức năng thành công.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% test kiểu dữ liệu (typing) Protocol và Duck typing của mypy hoàn tất không có lỗi.
  - [ ] Bộ Adapter Registry lọc và từ chối thành công các adapter sai giao thức.
  - [ ] Chế độ giảm cấp tính năng (degradation) hoạt động đúng khi cấu hình thiếu.
- **Phase 2 Exit Criteria**:
  - [ ] Plugin động được nạp và gỡ nạp (unload) thành công ra khỏi bộ nhớ trong quá trình kiểm thử mà không để lại rác tiến trình.
  - [ ] Các plugin không khớp phiên bản bị chặn nạp và ghi nhận lỗi vào log.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Đổi nhà cung cấp adapter bị lỗi hoặc gây gãy kiểu dữ liệu hàng loạt trong core.
  - *Steps*: Revert tệp cấu hình `adapters.yaml` về cấu hình mặc định (Playwright, SQLite), gỡ bỏ các tệp tin interface lỗi.
  - *Recovery*: Đảm bảo lõi khởi chạy lại bình thường sử dụng các adapter mặc định.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.7 | Yes | Yes | Yes | No | No | No | No |
| Task 1.9 | Yes | Yes | Yes | No | No | No | No |
| Task 1.11| Yes | Yes | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | Yes | Yes | Yes | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - `docs/designs/FEAT-057_vir_adapter_architecture_blueprint.md`
  - `docs/adr/ADR-008_python_protocols_adapter_interfaces.md` (Already generated)
- **Phase 2 Artifacts**:
  - `vir_runtime/adapters/loader.py`
  - `docs/guides/vir_plugin_development.md`

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích toàn bộ giao diện adapter tốn khoảng ~5,000 tokens.
- **Parallel execution opportunities**: Viết thiết kế các Protocol có thể làm hoàn toàn song song (Task 1.2 đến 1.6) vì các giao thức này độc lập.
- **Expected token savings**: Tiết kiệm ~30% tokens bằng cách viết các Protocol cô lập trong các tệp tin nhỏ và thực hiện kiểm tra kiểu tĩnh (mypy) thay vì chạy kiểm thử tích hợp thực tế có tải nặng.
- **Recommended execution strategy**: Hoàn thành sớm toàn bộ các tệp tin Protocol dưới thư mục `vir_runtime/adapters/base/` để làm nền tảng cho các FEAT quan sát tiếp theo.

---

## Recommended Next Skill
/blueprint
