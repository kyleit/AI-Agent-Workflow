<!-- File path: docs/plans/FEAT-063_vir_multi_agent_consensus_plan.md -->

---
feature_id: FEAT-063
feature_name: Visual Intelligence Runtime — Multi-Agent Architecture & Consensus Engine
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-063_vir_multi_agent_orchestration_and_consensus_engine.md
next_artifact: ../designs/FEAT-063_vir_multi_agent_consensus_blueprint.md
---

# FEAT-063: Visual Intelligence Runtime — Multi-Agent Architecture & Consensus Engine

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Model base Agent Contract requirements attributes | [x] |
| FR-03 | Phase 1 | Task 1.2 | Restrict inter-agent message exchanges to Event Bus only | [x] |
| FR-04 | Phase 1 | Task 1.3 | Build runtime validation schema constraints for agent registers | [x] |
| FR-05 | Phase 1 | Task 1.4 | Define dynamic status transition phases for agent lifecycles | [x] |
| FR-06 | Phase 1 | Task 1.5 | Implement weighted authority consensus evaluation math | [x] |
| FR-07 | Phase 1 | Task 1.6 | Map domain-specific authority weights mappings values | [x] |
| FR-08 | Phase 1 | Task 1.7 | Support veto allocations checks within domain topics | [x] |
| FR-09 | Phase 1 | Task 1.8 | Enforce validation requiring >= 1 evidence for active VETOs | [x] |
| FR-10 | Phase 1 | Task 1.9 | Define PASS gate criteria (no vetoes, high confidence) | [x] |
| FR-11 | Phase 1 | Task 1.10| Model structured `ConsensusRecord` output dataclass fields | [x] |
| FR-12 | Phase 1 | Task 1.11| Load consensus confidence thresholds from system parameters | [x] |
| FR-13 | Phase 1 | Task 1.12| Publish final verdict outputs to `vir.consensus.verdict` | [x] |
| FR-14 | Phase 1 | Task 1.13| Model core message envelope metadata headers | [x] |
| FR-15 | Phase 1 | Task 1.14| Enforce strict classification rules for event types | [x] |
| FR-16 | Phase 1 | Task 1.15| Implement timestamps checks filtering out stale messages | [x] |
| FR-02 | Phase 2 | Task 2.1 | Implement the 5-layer Agent Memory model | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Thiết lập cấu trúc Protocol và Dataclass của hợp đồng Agent.
- **Task 1.2**: [Verifier] - Triển khai bộ phân tích kiểm tra code tĩnh (linter), ngăn chặn hàm gọi trực tiếp giữa các agent.
- **Task 1.3**: [Coder] - Viết trình đăng ký agent (Registry) kiểm tra hợp lệ các chủ đề đăng ký nhận tin.
- **Task 1.4**: [Coder] - Cài đặt vòng đời agent từ DORMANT đến TERMINATED.
- **Task 1.5**: [Architect] - Thiết lập thuật toán bỏ phiếu lấy trọng số (weighted consensus algorithm).
- **Task 1.6**: [Coder] - Phân tích tệp tin cấu hình `vir_agents.yaml` để nạp các mức trọng số domain.
- **Task 1.7**: [Verifier] - Viết module lọc kiểm tra quyền VETO của agent trên các topic đăng ký.
- **Task 1.8**: [Verifier] - Chặn các yêu cầu VETO nếu mảng evidence đính kèm rỗng (chuyển sang ADVISORY).
- **Task 1.9**: [Architect] - Thiết kế biểu thức logic tổng hợp để trả kết quả PASS.
- **Task 1.10**: [Coder] - Tạo tệp tin Dataclass `ConsensusRecord` chứa đầy đủ cấu trúc lịch sử phiếu bầu.
- **Task 1.11**: [Coder] - Đồng bộ ngưỡng tin cậy mong muốn của dự án từ cấu hình.
- **Task 1.12**: [Coder] - Viết hàm phát hành tin nhắn phán quyết cuối cùng lên Event Bus.
- **Task 1.13**: [Architect] - Định dạng phong bì tin nhắn giao tiếp inter-agent.
- **Task 1.14**: [Coder] - Định kiểu enum cho các loại tin nhắn (EVIDENCE, VETO, VERDICT).
- **Task 1.15**: [Verifier] - Bộ lọc loại bỏ tin nhắn cũ có độ lệch thời gian > 500ms.
- **Task 2.1**: [Coder] - Triển khai 5 bộ nhớ thành phần của Agent, thiết lập đồng bộ hóa đĩa SQLite cho Long-term memory.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.3 -> Task 1.5 -> Task 1.7 -> Task 1.8 -> Task 1.10
- **Parallel Tasks**: [Task 1.2, Task 1.4], [Task 1.6, Task 1.11, Task 1.12], [Task 1.13, Task 1.14, Task 1.15], [Task 2.1]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.3), Task 1.5 (blocks Task 1.7), Task 2.1 (blocks agent initialization)
- **Independent Tasks**: Task 1.2, Task 1.15
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.3, Task 1.4 (Agent contract and runtime registry setup)
  - **Group 2**: Task 1.5, Task 1.6, Task 1.7, Task 1.8, Task 1.9, Task 1.10 (Consensus Engine algorithms core)
  - **Group 3**: Task 1.11, Task 1.12, Task 1.13, Task 1.14, Task 1.15 (Message bus communications protocol)
  - **Group 4**: Task 2.1 (Multi-layered agent memory model implementation)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/multi_agent/contract.py` | Create | Mô tả hợp đồng và thuộc tính của Agent |
| Task 1.3 | `vir_runtime/multi_agent/registry.py` | Modify | Tinh chỉnh bộ đăng ký và kiểm tra contract |
| Task 1.5 | `vir_runtime/multi_agent/consensus.py` | Create | Công cụ đồng thuận bỏ phiếu có trọng số |
| Task 1.6 | `vir_runtime/multi_agent/config.py` | Create | Đọc nạp tệp tin cấu hình `vir_agents.yaml` |
| Task 1.13| `vir_runtime/multi_agent/protocol.py` | Create | Đặc tả phong bì và giao tiếp liên agent |
| Task 2.1 | `vir_runtime/multi_agent/memory.py` | Create | Cài đặt mô hình bộ nhớ 5 phân lớp |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của `AgentContract`, `AgentRegistry`, `ConsensusEngine`, và `AgentMemory`.
- **Provider Pattern details**: Interface cho phép nạp các rule bỏ phiếu từ các tệp cấu hình động.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận phiếu bầu từ 5 domain -> Consensus thu thập -> nếu Design Agent phát lệnh VETO có bằng chứng -> kích hoạt hủy bỏ PASS -> đóng gói ConsensusRecord gửi Quality Gate.
- **Migration Strategy & Testing Architecture**: Sử dụng các agent giả lập (mock agents) với các trọng số domain cố định để kiểm tra tính đúng đắn của phép toán tổng hợp.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_agent_contracts.py` (Mapped to Task 1.3): Đảm bảo từ chối đăng ký các agent thiếu trường thông tin bắt buộc.
  - `tests/unit/test_weighted_consensus.py` (Mapped to Task 1.5): Thử nghiệm 3 phiếu PASS trọng số thấp đối đầu 1 phiếu VETO của Design Agent; đảm bảo phán quyết FAIL.
  - `tests/unit/test_unsupported_veto.py` (Mapped to Task 1.8): VETO không đính kèm evidence; đảm bảo phán quyết PASS được thông qua.
- **Integration Tests**:
  - `tests/integration/test_agent_memory.py` (Mapped to Task 2.1): Lưu thông số vào Long-term memory, tắt hệ thống, nạp lại và kiểm chứng khớp thông tin.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% kiểm thử toán bỏ phiếu trọng số và kiểm chứng VETO vượt qua.
  - [ ] Hệ thống từ chối nạp tin nhắn cũ quá 500ms.
  - [ ] VETO không có bằng chứng bị hạ cấp cảnh báo thành công.
- **Phase 2 Exit Criteria**:
  - [ ] Đọc và ghi nhận vết dữ liệu vào SQLite trong mô hình bộ nhớ 5 lớp hoạt động hoàn chỉnh.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Lỗi đồng thuận bỏ phiếu bị kẹt (deadlock) do chờ đợi phản hồi của agent VLM quá giờ.
  - *Steps*: Tích hợp cơ chế bỏ phiếu mặc định (default vote) quá giờ cho các agent không phản hồi, revert code `consensus.py`.
  - *Recovery*: Đảm bảo phán quyết kết luận luôn được đưa ra đúng thời hạn quy định.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.3 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.5 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Task 1.13| Yes | Yes | Yes | No | No | No | No |
| Task 2.1 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-063_vir_multi_agent_consensus_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/multi_agent/memory.py
- **Phase 3 Artifacts**: docs/adr/ADR-010_weighted_consensus.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch quản lý đồng thuận tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Viết protocol tin nhắn và nạp cấu hình (Task 1.6, 1.13) song song với lõi bỏ phiếu.
- **Expected token savings**: Tiết kiệm ~35% tokens bằng cách viết các bài kiểm tra logic bỏ phiếu trên mảng đầu vào tĩnh không nạp Playwright.
- **Recommended execution strategy**: Hoàn thành sớm phần thuật toán bỏ phiếu (consensus.py) trước khi viết cơ chế phân rã 5 tầng bộ nhớ.

---

## Recommended Next Skill
/blueprint
