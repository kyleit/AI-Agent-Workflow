<!-- File path: docs/plans/FEAT-054_fix_runtime_input_gate_plan.md -->

---
feature_id: FEAT-054
feature_name: Fix Runtime Input Gate Bug
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-054_fix_runtime_input_gate.md
next_artifact: ../designs/FEAT-054_fix_runtime_input_gate_blueprint.md
---

# FEAT-054: Fix Runtime Input Gate Bug

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Cơ chế tạm dừng và cập nhật trạng thái `waiting_input` trong session file | [x] |
| FR-02 | Phase 1 | Task 1.2 | Module sinh và xác thực `resume_token` bảo mật ngẫu nhiên | [x] |
| FR-03 | Phase 1 | Task 1.3 | Lệnh CLI hỗ trợ submit dữ liệu nhập liệu từ người dùng | [x] |
| FR-04 | Phase 1 | Task 1.4 | Bộ kiểm tra nguồn gốc đầu vào (Source Validation Engine) chặn AI tự xác nhận | [x] |
| FR-05 | Phase 1 | Task 1.5 | Cập nhật chính sách an toàn "Runtime Input Gate Policy" vào `AI_RULES.md` | [x] |
| NFR-02 | Phase 2 | Task 2.1 | Cơ chế bảo vệ và duy trì `conversation_id` khi ghi đè session | [x] |
| FR-06 | Phase 2 | Task 2.2 | Logic tự động làm sạch trường `pending_input` sau khi khôi phục luồng thành công | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1**: [Runtime Developer] - Thiết lập durable state `waiting_input` trong session.
- **Task 1.2**: [Security Specialist] - Triển khai sinh `resume_token` bảo mật.
- **Task 1.3**: [CLI Developer] - Phát triển interface submit dữ liệu qua CLI.
- **Task 1.4**: [Security Specialist] - Viết bộ lọc xác thực nguồn đầu vào.
- **Task 1.5**: [Technical Writer] - Soạn thảo chính sách an toàn trong `AI_RULES.md`.
- **Task 2.1**: [Runtime Developer] - Tương thích IDE Extension và duy trì hội thoại.
- **Task 2.2**: [Runtime Developer] - Xóa dữ liệu tạm khi khôi phục.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.4
- **Parallel Tasks**: [Task 1.5, Task 2.1]
- **Blocking Tasks**: Task 1.4 (blocks Task 2.2)
- **Independent Tasks**: Task 1.5
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2, Task 1.3, Task 1.4
  - Group 2: Task 1.5 (Parallel)
  - Group 3: Task 2.1, Task 2.2

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Thêm durable state `waiting_input` |
| Task 1.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Sinh và kiểm tra mã xác thực `resume_token` |
| Task 1.3 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Bổ sung sub-command `input submit` |
| Task 1.4 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Triển khai Source Validation Engine chặn nguồn `source=ai` |
| Task 1.5 | `AI_RULES.md` | Modify | Bổ sung "Runtime Input Gate Policy" vào mục chính sách an toàn |
| Task 2.1 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Tương thích và duy trì trường `conversation_id` trong session |
| Task 2.2 | `skills/workflow-runtime/scripts/workflow_runtime.py` | Modify | Làm sạch trường `pending_input` sau khi resume |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Thiết kế cấu trúc lớp `InputGate` và các phương thức `generate_token()`, `validate_source()`.
- **Provider Pattern details**: Không áp dụng.
- **Data Flow / Sequence Flow**: Vẽ luồng từ lúc CLI nhận lệnh -> sinh token -> dừng -> người dùng submit -> kiểm tra token -> chạy tiếp.
- **Migration Strategy & Testing Architecture**: Cung cấp mã kiểm thử unit test mock cho các loại nguồn đầu vào khác nhau.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: Viết các unit tests giả lập lệnh chạy yêu cầu input để kiểm tra status của session và kiểm tra ngoại lệ khi token sai (Mapped to Task 1.2 & Task 1.4).
- **Integration Tests**: Kiểm thử việc gửi lệnh CLI submit thành công và luồng khôi phục trạng thái hoàn tất (Mapped to Task 1.3 & Task 2.2).
- **Compatibility / Regression Tests**: Kiểm tra tính toàn vẹn của tệp `.session.json` và kiểm tra giá trị `conversation_id` (Mapped to Task 2.1).

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% các unit test kiểm tra chặn đầu vào từ AI chạy thành công.
  - [ ] Lệnh CLI `input submit` hoạt động đúng chuẩn, từ chối token sai.
  - [ ] Chính sách được tích hợp đầy đủ vào `AI_RULES.md`.
- **Phase 2 Exit Criteria**:
  - [ ] Dữ liệu `pending_input` tự động được dọn dẹp sạch sẽ sau khi resume.
  - [ ] `conversation_id` được bảo toàn xuyên suốt.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Runtime bị treo cứng hoặc lỗi cú pháp python không thể khởi chạy CLI.
  - Steps: Dùng git checkout để hoàn tác thay đổi trên `workflow_runtime.py`, khôi phục tệp `AI_RULES.md` về trạng thái ban đầu.
  - Recovery: Xác nhận CLI hoạt động lại bình thường và kiểm tra trạng thái session cũ.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | Yes | No | No | No | No |
| Task 1.4 | Yes | Yes | Yes | No | No | No | No |
| Task 1.5 | Yes | No | No | No | Yes | Yes | No |
| Task 2.1 | Yes | Yes | Yes | Yes | No | No | No |
| Task 2.2 | Yes | Yes | Yes | No | No | No | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-054_fix_runtime_input_gate_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-054_input_gate_security.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Các công việc lõi được thực hiện tuần tự để tránh xung đột mã nguồn.
- **Parallel execution opportunities**: Có thể viết tài liệu chính sách `AI_RULES.md` song song với việc phát triển code.
- **Expected token savings**: Giảm thiểu token tiêu thụ nhờ loại bỏ hoàn toàn các vòng lặp tự động xác nhận sai lệch của AI.

## Recommended Next Skill
/blueprint
