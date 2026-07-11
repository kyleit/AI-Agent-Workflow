<!-- File path: docs/plans/FEAT-055_vir_vision_goals_and_architectural_foundation_plan.md -->

---
feature_id: FEAT-055
feature_name: Visual Intelligence Runtime — Vision, Goals & Architectural Foundation
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-055_vir_vision_goals_and_architectural_foundation.md
next_artifact: ../designs/FEAT-055_vir_vision_goals_and_architectural_foundation_blueprint.md
---

# FEAT-055: Visual Intelligence Runtime — Vision, Goals & Architectural Foundation

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Establish standalone run mechanics separate from thin client | [x] |
| FR-02 | Phase 1 | Task 1.2 | Define the perception-first pipeline flow stages in Orchestrator | [x] |
| FR-03 | Phase 1 | Task 1.3 | Model the multi-dimensional structure parameters of the Digital Twin | [x] |
| FR-04 | Phase 1 | Task 1.4 | Outline parameters for local CLI, IDE visualizer, CI, and daemon execution | [x] |
| FR-05 | Phase 1 | Task 1.5 | Establish active agent mapping rules for adaptive profiling | [x] |
| FR-06 | Phase 1 | Task 1.6 | Set up structural provider interface boundaries for swappable backends | [x] |
| FR-07 | Phase 1 | Task 1.7 | Enforce strict boundaries allocating intelligence rules to the core | [x] |
| FR-08 | Phase 1 | Task 1.8 | Formalize core agent contract schema checks | [x] |
| FR-09 | Phase 2 | Task 2.1 | Map milestone schedules for subsequent sensory, design, and memory phases | [x] |
| FR-10 | Phase 2 | Task 2.2 | Configure JSON and Markdown structure options for diagnostic reporting | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai lõi thực thi tách rời của VIR để nhận lệnh độc lập.
- **Task 1.2**: [Architect] - Định nghĩa chi tiết các pha xử lý tuần tự của pipeline nhận thức.
- **Task 1.3**: [Architect] - Thiết lập cấu trúc dữ liệu mô hình hóa 11 chiều trạng thái của Digital Twin.
- **Task 1.4**: [Coder] - Định cấu hình cấu trúc tham số đầu vào cho 4 chế độ chạy của hệ thống.
- **Task 1.5**: [Architect] - Ánh xạ danh sách các agent được kích hoạt tương ứng với mỗi Profile hiệu năng.
- **Task 1.6**: [Architect] - Thiết lập các Protocol giao tiếp trung gian, đảm bảo tính tách rời nhà cung cấp.
- **Task 1.7**: [Verifier] - Thiết lập các bài kiểm tra ranh giới để ngăn logic nghiệp vụ lọt vào thin client.
- **Task 1.8**: [Coder] - Xây dựng bộ kiểm tra hợp đồng Agent trước khi đăng ký vào hệ thống.
- **Task 2.1**: [Documentation] - Xây dựng tài liệu hướng dẫn tích hợp lộ trình và tiến độ các pha tiếp theo.
- **Task 2.2**: [Coder] - Định nghĩa cấu trúc mẫu xuất bản báo cáo (Markdown & JSON Schema).

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3
- **Parallel Tasks**: [Task 1.4, Task 1.5], [Task 1.6, Task 1.7, Task 1.8]
- **Blocking Tasks**: Task 1.3 (blocks Task 1.5), Task 1.6 (blocks Task 1.8)
- **Independent Tasks**: Task 2.1, Task 2.2
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3 (Sequential core bootstrap)
  - **Group 2**: Task 1.4, Task 1.5 (Parallel configuration parameters mapping)
  - **Group 3**: Task 1.6, Task 1.7, Task 1.8 (Parallel adapter abstraction & safety verification)
  - **Group 4**: Task 2.1, Task 2.2 (Parallel documentation & reporting setup)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/core/runtime.py` | Create | Thiết lập điểm chạy độc lập của runtime |
| Task 1.2 | `vir_runtime/core/orchestrator.py` | Create | Quản lý vòng đời chạy tuần tự của pipeline nhận thức |
| Task 1.3 | `vir_runtime/domain/twin.py` | Create | Định nghĩa mô hình lưu giữ trạng thái Digital Twin |
| Task 1.4 | `vir_runtime/core/execution.py` | Create | Quản lý tham số và ranh giới cho các Execution Modes |
| Task 1.5 | `vir_runtime/core/profiles.py` | Create | Ánh xạ và kích hoạt các Profile hiệu năng tương ứng |
| Task 1.6 | `vir_runtime/adapters/base/` | Create | Chứa các Protocol giao diện Adapter cốt lõi |
| Task 1.7 | `.agents/skills/frontend-visual-debug/SKILL.md` | Modify | Tinh giản skill cũ thành thin client gọi qua CLI của VIR |
| Task 1.8 | `vir_runtime/domain/agent_contract.py` | Create | Cài đặt cấu trúc xác thực hợp đồng Agent |
| Task 2.1 | `docs/guides/vir_integration_guide.md` | Create | Tài liệu hướng dẫn tích hợp lộ trình phát triển |
| Task 2.2 | `vir_runtime/domain/report_schema.json` | Create | Khai báo JSON Schema mẫu cho báo cáo kết quả |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Định nghĩa các Interface lớp của `VIRRuntimeCore`, `LifecycleOrchestrator`, và `AgentRegistry`.
- **Provider Pattern details**: Thiết lập cấu trúc giao thức của các lớp base Adapter, che giấu các chi tiết kết nối của Selenium, Playwright hay Puppeteer.
- **Data Flow / Sequence Flow**: Mô hình hóa chuỗi sự kiện truyền phát qua bus khi Orchestrator chuyển trạng thái nhận thức.
- **Migration Strategy & Testing Architecture**: Phương án di chuyển logic E2E cũ sang giao thức mỏng, sử dụng mock framework để chạy thử lõi mà không cần nạp Playwright thực tế.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_runtime_init.py` (Mapped to Task 1.1): Xác thực nạp cấu hình và khởi chạy lõi runtime.
  - `tests/unit/test_agent_contracts.py` (Mapped to Task 1.8): Đảm bảo các mock agent sai hợp đồng bị từ chối đăng ký.
  - `tests/unit/test_profiles_mapping.py` (Mapped to Task 1.5): Kiểm tra bật/tắt đúng tập hợp agent tương ứng với các profile.
- **Integration Tests**:
  - `tests/integration/test_thin_client_delegation.py` (Mapped to Task 1.7): Kiểm thử mock client gọi qua CLI của VIR và nhận phản hồi đúng cấu trúc.
- **Compatibility / Regression Tests**:
  - Đảm bảo các script E2E cũ gọi skill `frontend-visual-debug` không bị gãy giao diện tham số truyền vào.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các bài test đơn vị cho khởi tạo core, nạp profile, và hợp đồng agent vượt qua (Pass).
  - [ ] Lõi `vir_runtime` khởi chạy độc lập được bằng CLI mà không bị phụ thuộc vào các tệp tin của skill.
  - [ ] Đã rút gọn thành công logic của `frontend-visual-debug` SKILL.md về dạng gọi trung gian.
- **Phase 2 Exit Criteria**:
  - [ ] JSON Schema báo cáo kết quả được phát hành và vượt qua kiểm tra cấu trúc.
  - [ ] Có đầy đủ tài liệu hướng dẫn tích hợp lộ trình phát triển.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Lỗi biên dịch core nghiêm trọng khiến tất cả E2E test cũ trong dự án bị ngắt quãng.
  - *Steps*: Revert các tệp tin core trong thư mục `vir_runtime`, khôi phục bản sao lưu của `frontend-visual-debug` SKILL.md.
  - *Recovery*: Đảm bảo các workflow cũ phục hồi lại trạng thái kiểm thử procedural của skill ban đầu.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | No | No | No | Yes | Yes |
| Task 1.7 | Yes | No | Yes | Yes | Yes | No | No |
| Task 1.8 | Yes | Yes | Yes | No | No | No | No |
| Task 2.2 | Yes | No | No | Yes | Yes | No | Yes |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**:
  - `docs/designs/FEAT-055_vir_vision_goals_and_architectural_foundation_blueprint.md`
- **Phase 2 Artifacts**:
  - `docs/guides/vir_integration_guide.md`
  - `vir_runtime/domain/report_schema.json`

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: 100% tuần tự sẽ tốn trung bình ~6,000 tokens cho mỗi lần nạp lại ngữ cảnh thiết kế.
- **Parallel execution opportunities**: Chạy song song thiết kế các module Interface và kiểm tra an toàn client giúp rút ngắn thời gian phản hồi.
- **Expected token savings**: Tiết kiệm ~35% tokens bằng cách sử dụng các tệp mock adapter có dung lượng nhỏ thay vì nạp toàn bộ thư viện Playwright vào ngữ cảnh của Coder Agent.
- **Recommended execution strategy**: Hoàn thành sớm nhóm Interface và Mock Adapter trước khi tiến hành viết code lõi thực tế.

---

## Recommended Next Skill
/blueprint
