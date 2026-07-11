<!-- File path: docs/plans/FEAT-069_vir_sdlc_integration_plan.md -->

---
feature_id: FEAT-069
feature_name: Visual Intelligence Runtime — SDLC Integration & Future AI Capabilities Roadmap
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-069_vir_sdlc_integration_and_future_ai_capabilities.md
next_artifact: ../designs/FEAT-069_vir_sdlc_integration_blueprint.md
---

# FEAT-069: Visual Intelligence Runtime — SDLC Integration & Future AI Capabilities Roadmap

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Bind VIR checks at the 4 SDLC workflow checkpoints | [x] |
| FR-02 | Phase 1 | Task 1.2 | Integrate quality block gates within the AIWF Approval Gate | [x] |
| FR-03 | Phase 1 | Task 1.3 | Update workflow checkpoint states on validation success | [x] |
| FR-04 | Phase 1 | Task 1.4 | Direct report paths output to `docs/verification/` folder | [x] |
| FR-05 | Phase 1 | Task 1.5 | Load execution context values from specifications | [x] |
| FR-06 | Phase 1 | Task 1.6 | Block code modifications tasks targeting files outside scope | [x] |
| FR-07 | Phase 1 | Task 1.7 | Enforce AIWF Artifact Policy parameters | [x] |
| FR-14 | Phase 1 | Task 1.8 | Outline extension mechanisms for new adapters and agents | [x] |
| FR-15 | Phase 1 | Task 1.9 | Protect core from modifications when adding new capabilities | [x] |
| FR-21 | Phase 1 | Task 1.10| Model capability registration descriptors fields | [x] |
| FR-22 | Phase 1 | Task 1.11| Enforce explicit user consent verification checks | [x] |
| FR-08 | Phase 2 | Task 2.1 | Map Coder Agent interaction commands pipelines | [x] |
| FR-09 | Phase 2 | Task 2.2 | Map Reviewer Agent verification evidence feeds | [x] |
| FR-10 | Phase 2 | Task 2.3 | Connect Planner Agent risk logs input feeds | [x] |
| FR-11 | Phase 2 | Task 2.4 | Connect Architect Agent Digital Twin validation parameters | [x] |
| FR-12 | Phase 2 | Task 2.5 | Map Release Manager Agent publish validation gates | [x] |
| FR-13 | Phase 2 | Task 2.6 | Map Debug Skill initial evidence gather commands | [x] |
| FR-16 | Phase 2 | Task 2.7 | Support Local Vision Model (VLM) adapters overlays | [x] |
| FR-17 | Phase 2 | Task 2.8 | Support Cloud VLM adapter key override configs | [x] |
| FR-18 | Phase 2 | Task 2.9 | Support LLM based planning agent contracts registrations | [x] |
| FR-19 | Phase 2 | Task 2.10| Map specialized performance and QA observers contracts | [x] |
| FR-20 | Phase 2 | Task 2.11| Support Security Review veto engine triggers | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Tích hợp lệnh gọi VIR vào 4 tập lệnh tương ứng của workflow runtime.
- **Task 1.2**: [Verifier] - Triển khai chặn duyệt approval gate nếu kết quả kiểm định VIR là FAIL.
- **Task 1.3**: [Coder] - Viết mã cập nhật phiên `.session.json` của workflow khi vượt qua VIR PASS.
- **Task 1.4**: [Coder] - Cấu hình đường dẫn xuất Markdown báo cáo tương thích quy chuẩn verification.
- **Task 1.5**: [Coder] - Lấy các giá trị (blueprint path, feature ID) nạp vào cấu hình chạy VIR.
- **Task 1.6**: [Verifier] - Chặn biên dịch và chạy thử các tệp mã nguồn nằm ngoài phạm vi Blueprint.
- **Task 1.7**: [Verifier] - Đảm bảo các tệp tin kết xuất (zip, NDJSON) có đầy đủ liên kết Feature ID.
- **Task 1.8**: [Architect] - Xây dựng tài liệu hướng dẫn và các mẫu lớp (templates) mở rộng adapter/agent.
- **Task 1.9**: [Verifier] - Quét mã kiểm thử (static test audit) đảm bảo nạp agent ngoài không sửa tệp tin lõi.
- **Task 1.10**: [Architect] - Khai báo cấu trúc mô tả năng lực của adapter ngoài (cost_tier, privacy_level).
- **Task 1.11**: [Verifier] - Triển khai bộ chặn kiểm tra, ném lỗi bắt buộc xác nhận consent nếu dùng cloud VLM.
- **Task 2.1**: [Coder] - Định luồng gọi tự động VIR Standard sau mỗi mốc viết code của Coder.
- **Task 2.2**: [Coder] - Tích hợp VIR Deep report làm bằng chứng kiểm thử của Reviewer.
- **Task 2.3**: [Coder] - Nạp báo cáo lỗi cũ vào tri thức lập kế hoạch của Planner.
- **Task 2.4**: [Architect] - Liên kết dữ liệu Digital Twin cho các bài xác thực kiến trúc của Architect.
- **Task 2.5**: [Coder] - Enforce luồng chạy VIR CI bắt buộc trước khi Release Manager xuất bản.
- **Task 2.6**: [Coder] - Cài đặt gọi VIR Lightweight khi khởi chạy Debug skill.
- **Task 2.7**: [Coder] - Triển khai nạp các mô hình vision cục bộ qua Ollama.
- **Task 2.8**: [Coder] - Hỗ trợ nạp token API của GPT-4V hoặc Gemini qua biến môi trường.
- **Task 2.9**: [Architect] - Đặc tả hợp đồng cho các Agent suy đoán lập kế hoạch bằng mô hình lớn.
- **Task 2.10**: [Coder] - Viết template đăng ký các observer chuyên biệt.
- **Task 2.11**: [Verifier] - Cấu hình mức độ phủ quyết VETO tuyệt đối của Security Agent trên topic `security`.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.6 -> Task 1.9 -> Task 2.5
- **Parallel Tasks**: [Task 1.4, Task 1.5, Task 1.7], [Task 1.8, Task 1.10, Task 1.11], [Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.6], [Task 2.7, Task 2.8, Task 2.9, Task 2.10, Task 2.11]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.3), Task 1.8 (blocks Task 1.9), Task 2.7 (blocks Task 2.8)
- **Independent Tasks**: Task 1.11, Task 2.3
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.6 (Workflow runtime checkpoints & approval gates)
  - **Group 2**: Task 1.4, Task 1.5, Task 1.7, Task 1.11 (Artifact policies and context parser checks)
  - **Group 3**: Task 1.8, Task 1.9, Task 1.10 (Extensibility and safety capabilities validator)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5, Task 2.6 (AIWF Agents integrations)
  - **Group 5**: Task 2.7, Task 2.8, Task 2.9, Task 2.10, Task 2.11 (Future AI models and QA observers setups)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Tích hợp các mốc gọi VIR |
| Task 1.2 | `.agents/skills/workflow-runtime/scripts/session.py` | Modify | Quản lý khóa cổng duyệt gate |
| Task 1.11| `vir_runtime/core/consent.py` | Create | Trình kiểm tra sự đồng ý (consent) gửi cloud |
| Task 2.1 | `.agents/skills/implementation-to-debug/SKILL.md` | Modify | Tinh chỉnh logic gọi VIR khi gỡ lỗi |
| Task 2.5 | `.agents/skills/implementation-to-release/SKILL.md` | Modify | Chèn cổng kiểm thử CI bắt buộc trước khi phát hành |
| Task 2.7 | `vir_runtime/adapters/vision/ollama.py` | Create | Adapter vision cục bộ sử dụng Ollama |
| Task 2.8 | `vir_runtime/adapters/vision/gemini.py` | Create | Adapter vision đám mây sử dụng Gemini API |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Cấu trúc tích hợp giữa `WorkflowRuntime` và `VIRCoreOrchestrator`.
- **Provider Pattern details**: Định cấu hình khóa quyền (consents) và phân cấp chi phí (cost tiers) trong `adapters.yaml`.
- **Data Flow / Sequence Flow**: Vẽ luồng khi chạy Coder hoàn tất -> gọi workflow_runtime -> kích hoạt VIR Standard -> ghi nhận pass -> cập nhật checkpoint -> mở khóa approval gate.
- **Migration Strategy & Testing Architecture**: Viết các bài test tích hợp giả định (mock runs) trên workflow runtime để đo tốc độ chuyển đổi checkpoints.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_cloud_consent.py` (Mapped to Task 1.11): Bật cloud adapter nhưng gán consent=False; đảm bảo raises lỗi chặn chạy.
  - `tests/unit/test_extension_isolation.py` (Mapped to Task 1.9): Thử thêm một mock agent mới; xác nhận code lõi không bị thay đổi.
- **Integration Tests**:
  - `tests/integration/test_approval_gate_block.py` (Mapped to Task 1.2): Trình chạy thử một kịch bản kiểm định thất bại (FAIL); xác nhận approval gate bị khóa chặt không cho bấm proceed.
  - `tests/integration/test_checkpoint_advance.py` (Mapped to Task 1.3): Khởi chạy thành công kịch bản PASS; xác thực trạng thái phiên workflow nâng lên checkpoint tiếp theo.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Khóa an toàn block gate hoạt động chính xác khi gặp kết quả FAIL.
  - [ ] Chuyển tiếp thành công các checkpoint trên tệp tin phiên sau khi chạy PASS.
  - [ ] Báo lỗi từ chối chạy ngay lập tức nếu cloud VLM được kích hoạt mà không có sự đồng ý của con người.
- **Phase 2 Exit Criteria**:
  - [ ] Cài đặt thành công adapter kết nối Gemini API mà không thay đổi bất kỳ tệp tin lõi nào của orchestrator.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Lỗi đồng bộ checkpoint gây gãy trạng thái phiên kiểm thử, khóa cứng không cho Coder Agent tiến hành công việc.
  - *Steps*: Tạm tắt cơ chế đồng bộ checkpoint bắt buộc, revert mã nguồn `workflow_runtime.py`, khôi phục bản sao lưu cũ.
  - *Recovery*: Đảm bảo các tiến trình SDLC tiếp tục chạy bằng các checkpoint thủ công của hệ thống cũ.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | Yes | Yes | Yes | Yes | Yes |
| Task 1.2 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.11| Yes | Yes | Yes | No | Yes | No | No |
| Task 2.5 | Yes | No | Yes | Yes | Yes | No | No |
| Task 2.8 | Yes | Yes | Yes | No | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-069_vir_sdlc_integration_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/adapters/vision/gemini.py
- **Phase 3 Artifacts**: docs/adr/ADR-021_sdlc_checkpoints.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch SDLC integration tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm viết các adapter mô hình vision (Task 2.7, 2.8) chạy song song với phần tích hợp agents.
- **Expected token savings**: Tiết kiệm ~45% tokens nhờ chạy các kiểm thử tích hợp trên mock session file không khởi động tiến trình con Playwright.
- **Recommended execution strategy**: Hoàn thành sớm phần chặn approval gate (session.py) trước khi viết các adapter kết nối cloud API phức tạp.

---

## Recommended Next Skill
/blueprint
