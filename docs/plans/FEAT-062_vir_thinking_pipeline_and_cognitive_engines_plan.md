<!-- File path: docs/plans/FEAT-062_vir_thinking_pipeline_and_cognitive_engines_plan.md -->

---
feature_id: FEAT-062
feature_name: Visual Intelligence Runtime — Thinking Pipeline & Cognitive Engines
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-062_vir_thinking_pipeline_and_cognitive_engines.md
next_artifact: ../designs/FEAT-062_vir_thinking_pipeline_and_cognitive_engines_blueprint.md
---

# FEAT-062: Visual Intelligence Runtime — Thinking Pipeline & Cognitive Engines

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Implement the 11-stage Thinking Pipeline execution flow | [x] |
| FR-02 | Phase 1 | Task 1.2 | Integrate per-stage execution timeouts handlers | [x] |
| FR-03 | Phase 1 | Task 1.3 | Enforce maximum rethink limits and hypothesis counts | [x] |
| FR-04 | Phase 1 | Task 1.4 | Implement transition parameters to state BLOCKED | [x] |
| FR-06 | Phase 1 | Task 1.5 | Publish stage transition logs events to the Event Bus | [x] |
| FR-07 | Phase 1 | Task 1.6 | Create Contradiction Detection Engine event listener | [x] |
| FR-08 | Phase 1 | Task 1.7 | Construct structured ContradictionRecord model fields | [x] |
| FR-09 | Phase 1 | Task 1.8 | Inject ContradictionRecords as Symptoms into Investigations | [x] |
| FR-10 | Phase 1 | Task 1.9 | Classify contradiction severity levels (possible/confirmed) | [x] |
| FR-11 | Phase 1 | Task 1.10| Integrate Self-Doubt Engine trigger handlers | [x] |
| FR-12 | Phase 1 | Task 1.11| Challenge conclusions based on single-signal checks | [x] |
| FR-13 | Phase 1 | Task 1.12| Enforce bounded re-observation loop counts limit | [x] |
| FR-14 | Phase 1 | Task 1.13| Support dynamic investigation strategy change routes | [x] |
| FR-16 | Phase 1 | Task 1.14| Escalate block issues asking for human confirmation | [x] |
| FR-17 | Phase 1 | Task 1.15| Create Root Cause Analysis (RCA) Engine core | [x] |
| FR-18 | Phase 1 | Task 1.16| Enforce validator checks requiring >= 2 independent evidence | [x] |
| FR-19 | Phase 1 | Task 1.17| Model RCA category classification codes | [x] |
| FR-20 | Phase 1 | Task 1.18| Model structured RootCause object metadata fields | [x] |
| FR-21 | Phase 1 | Task 1.19| Verify fix requests are within blueprint-approved scope | [x] |
| FR-05 | Phase 2 | Task 2.1 | Support parallel testing of independent hypotheses | [x] |
| FR-15 | Phase 2 | Task 2.2 | Build strategy overrides list mapping reactive bindings | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Thiết lập sơ đồ máy trạng thái bất đồng bộ cho 11 bước Thinking Pipeline.
- **Task 1.2**: [Coder] - Viết trình đếm giờ giới hạn (timeout decorator) cho từng bước xử lý.
- **Task 1.3**: [Verifier] - Triển khai bộ đếm chặn vòng lặp suy nghĩ lại (rethink) vượt quá 3 lượt.
- **Task 1.4**: [Coder] - Định cấu hình chuyển trạng thái OPEN sang BLOCKED kèm báo cáo thô.
- **Task 1.5**: [Coder] - Phát đi tin nhắn trạng thái `pipeline.stage_transition` lên bus.
- **Task 1.6**: [Coder] - Đăng ký lắng nghe sự kiện không đồng bộ của Digital Twin và Evidence.
- **Task 1.7**: [Architect] - Định nghĩa cấu trúc `ContradictionRecord`.
- **Task 1.8**: [Coder] - Cập nhật tự động mâu thuẫn vào mảng triệu chứng (symptoms) của Investigation.
- **Task 1.9**: [Verifier] - Cài đặt logic phân cấp độ mâu thuẫn (Timing vs Confirmed).
- **Task 1.10**: [Coder] - Viết module kích hoạt Self-Doubt Engine khi nhận tín hiệu cảnh báo.
- **Task 1.11**: [Verifier] - Triển khai hạ mức điểm tin cậy nếu dữ liệu kết luận từ một nguồn duy nhất.
- **Task 1.12**: [Coder] - Thiết lập vòng lặp quan sát lại (re-observe) tối đa 3 lần.
- **Task 1.13**: [Architect] - Viết cấu trúc lựa chọn đổi chiến lược điều tra (switch strategy).
- **Task 1.14**: [Runtime] - Tinh chỉnh cổng dừng chờ người dùng phê duyệt (approval gate) trước các hành động phá hủy.
- **Task 1.15**: [Coder] - Triển khai module RCA thu thập giả thuyết đã xác thực.
- **Task 1.16**: [Verifier] - Chặn kết luận nguyên nhân gốc nếu số lượng evidence liên kết < 2.
- **Task 1.17**: [Architect] - Phân nhóm các mã lỗi (TIMING, ROUTING, CSS_SPECIFICITY, etc.).
- **Task 1.18**: [Coder] - Khai báo Dataclass `RootCause`.
- **Task 1.19**: [Verifier] - Kiểm chứng phạm vi sửa đổi tệp tin dựa trên Blueprint đã nạp.
- **Task 2.1**: [Coder] - Sử dụng `asyncio.gather` chạy đồng thời các bài kiểm tra giả thuyết độc lập.
- **Task 2.2**: [Documentation] - Soạn tài liệu mô tả các bài phân tích sâu (derived state, race conditions).

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.10 -> Task 1.13 -> Task 1.15 -> Task 1.16
- **Parallel Tasks**: [Task 1.2, Task 1.3, Task 1.4], [Task 1.6, Task 1.7, Task 1.8], [Task 1.17, Task 1.18, Task 1.19], [Task 2.1, Task 2.2]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.10), Task 1.10 (blocks Task 1.13), Task 1.15 (blocks Task 1.16)
- **Independent Tasks**: Task 1.5, Task 1.14
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.5 (Thinking Pipeline state orchestrator)
  - **Group 2**: Task 1.6, Task 1.7, Task 1.8, Task 1.9 (Contradiction Detection engine)
  - **Group 3**: Task 1.10, Task 1.11, Task 1.12, Task 1.13 (Self-Doubt engine logic & retries)
  - **Group 4**: Task 1.15, Task 1.16, Task 1.17, Task 1.18, Task 1.19, Task 1.14 (RCA and action validation)
  - **Group 5**: Task 2.1, Task 2.2 (Parallel testings & overrides logs)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/cognitive/pipeline.py` | Create | Trình điều khiển tuần tự 11 bước suy nghĩ |
| Task 1.6 | `vir_runtime/cognitive/contradiction.py` | Create | Trình phát hiện và ghi nhận mâu thuẫn |
| Task 1.10| `vir_runtime/cognitive/doubt.py` | Create | Trình tự nghi ngờ và tính toán lại độ tin cậy |
| Task 1.15| `vir_runtime/cognitive/rca.py` | Create | Trình phân tích nguyên nhân gốc (RCA) |
| Task 1.19| `vir_runtime/cognitive/safety_checker.py`| Create | Xác minh phạm vi chỉnh sửa so với Blueprint |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Cấu trúc các lớp `ThinkingPipeline`, `ContradictionEngine`, `SelfDoubtManager`, và `RCAEngine`.
- **Provider Pattern details**: Mẫu giao tiếp event-driven che giấu các bộ lọc heuristic.
- **Data Flow / Sequence Flow**: Vẽ luồng khi phát hiện mâu thuẫn -> kích hoạt nghi ngờ -> re-observe -> nếu không đổi -> đổi chiến lược -> tìm ra nguyên nhân gốc -> so khớp scope -> đề xuất sửa đổi.
- **Migration Strategy & Testing Architecture**: Chạy thử nghiệm bằng cách tiêm (inject) các chuỗi sự kiện mâu thuẫn giả định để đánh giá hành vi quyết định của máy trạng thái.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_thinking_pipeline.py` (Mapped to Task 1.1): Xác thực chuyển tiếp 11 bước thành công trên kịch bản xanh (happy path).
  - `tests/unit/test_self_doubt_retry.py` (Mapped to Task 1.12): Inject lỗi mạng tạm thời; xác nhận hệ thống chạy re-observe thành công và giải quyết nghi ngờ.
  - `tests/unit/test_rca_gate.py` (Mapped to Task 1.16): Kiểm thử từ chối ra nguyên nhân gốc nếu chỉ có 1 evidence hỗ trợ.
- **Integration Tests**:
  - `tests/integration/test_scope_protection.py` (Mapped to Task 1.19): Trình sửa đổi thử viết code ngoài phạm vi Blueprint; xác nhận safety checker chặn đứng hành vi.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các bước chuyển trạng thái pipeline chạy trơn tru trong < 100ms.
  - [ ] Hệ thống chặn thành công các hành động thay đổi code ngoài Blueprint.
  - [ ] Ngắt vòng lặp vô hạn (infinite loop) thành công sau đúng 3 chu kỳ Re-think.
- **Phase 2 Exit Criteria**:
  - [ ] Hỗ trợ kiểm thử giả thuyết song song sử dụng asyncio hoàn tất không có lỗi xung đột tài nguyên.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Đổi chiến lược tự động (strategy change) làm đảo lộn trạng thái trình duyệt liên tục gây treo hệ thống.
  - *Steps*: Revert cơ chế tự thay đổi chiến lược, gán cứng quay về kiểm tra DOM mặc định, khôi phục code `doubt.py`.
  - *Recovery*: Đảm bảo hệ thống dừng và báo cáo thay vì tiếp tục đổi chiến lược gây nghẽn CI.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Task 1.6 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.10| Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.15| Yes | Yes | Yes | No | Yes | Yes | Yes |
| Task 1.19| Yes | Yes | Yes | No | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-062_vir_thinking_pipeline_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-012_cognitive_reasoning.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích logic tư duy tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Viết cấu trúc Contradiction và kiểm tra an toàn (Task 1.7, 1.19) song song với lõi pipeline.py.
- **Expected token savings**: Tiết kiệm ~35% tokens bằng cách viết các bài kiểm tra giả định cho rca.py trên SQLite đĩa cứng lưu vết giả thay vì mở các phiên Web thực tế.
- **Recommended execution strategy**: Hoàn thiện sớm bộ kiểm tra an toàn (safety_checker.py) và rca.py trước khi cài đặt logic nghi ngờ phức tạp.

---

## Recommended Next Skill
/blueprint
