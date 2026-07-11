<!-- File path: docs/plans/FEAT-060_vir_digital_twin_plan.md -->

---
feature_id: FEAT-060
feature_name: Visual Intelligence Runtime — Digital Twin & Application State Model
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-060_vir_digital_twin_and_application_state_model.md
next_artifact: ../designs/FEAT-060_vir_digital_twin_blueprint.md
---

# FEAT-060: Visual Intelligence Runtime — Digital Twin & Application State Model

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Model and map the 11 dimension fields inside the Digital Twin | [x] |
| FR-02 | Phase 1 | Task 1.2 | Implement state update handlers listening to sensory evidence events | [x] |
| FR-03 | Phase 1 | Task 1.3 | Create consistency checker detecting cross-dimension conflicts | [x] |
| FR-04 | Phase 1 | Task 1.4 | Publish `twin.inconsistency.detected` events to Event Bus | [x] |
| FR-05 | Phase 1 | Task 1.5 | Implement circular update history buffers | [x] |
| FR-06 | Phase 1 | Task 1.6 | Implement health index scoring computation algorithms | [x] |
| FR-07 | Phase 1 | Task 1.7 | Implement SQLite serialization/deserialization for Digital Twin states | [x] |
| FR-08 | Phase 1 | Task 1.8 | Support thread-safe partial updates via asyncio locks | [x] |
| FR-09 | Phase 1 | Task 1.9 | Define query APIs for dimension lookups | [x] |
| FR-10 | Phase 2 | Task 2.1 | Implement dimension staleness checks and trigger timeout warnings | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Đặc tả cấu trúc chi tiết 11 chiều trạng thái của Digital Twin.
- **Task 1.2**: [Coder] - Cài đặt subscriber bắt các tin sự kiện và cập nhật vào mô hình.
- **Task 1.3**: [Architect] - Xây dựng các quy tắc khai báo (declarative rules) để phát hiện mâu thuẫn chéo.
- **Task 1.4**: [Coder] - Phát hành sự kiện khi phát hiện không nhất quán trong mô hình.
- **Task 1.5**: [Coder] - Triển khai bộ đệm lưu giữ 50 bản ghi thay đổi gần nhất cho mỗi chiều.
- **Task 1.6**: [Verifier] - Phát triển thuật toán trừ điểm tin cậy dựa trên số lượng mâu thuẫn phát sinh.
- **Task 1.7**: [Coder] - Thiết lập bảng `vir_digital_twin` trong SQLite phục vụ lưu lưu trữ.
- **Task 1.8**: [Coder] - Tích hợp khóa asyncio bảo vệ tranh chấp dữ liệu khi cập nhật song song.
- **Task 1.9**: [Architect] - Xây dựng API truy vấn ngữ cảnh thân thiện cho các agent bên ngoài.
- **Task 2.1**: [Verifier] - Triển khai background task theo dõi độ trễ cập nhật và phát cảnh báo hết hạn (stale).

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.6
- **Parallel Tasks**: [Task 1.5, Task 1.7], [Task 1.8, Task 1.9], [Task 2.1]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.9), Task 1.3 (blocks Task 1.4)
- **Independent Tasks**: Task 1.7, Task 2.1
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.6 (Core state update and consistency engine)
  - **Group 2**: Task 1.5, Task 1.7, Task 1.8 (Storage and thread safety controls)
  - **Group 3**: Task 1.9, Task 2.1 (Queries and staleness monitoring)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/domain/twin.py` | Modify | Cập nhật cấu trúc 11 chiều của twin |
| Task 1.3 | `vir_runtime/twin/consistency.py` | Create | Trình kiểm tra mâu thuẫn chéo |
| Task 1.5 | `vir_runtime/twin/history.py` | Create | Lưu vết cập nhật (history buffer) |
| Task 1.7 | `vir_runtime/twin/persistence.py` | Create | Serialization/deserialization vào SQLite |
| Task 1.9 | `vir_runtime/twin/query.py` | Create | Cung cấp giao thức truy vấn |
| Task 2.1 | `vir_runtime/twin/stale_monitor.py` | Create | Trình giám sát độ cũ của dữ liệu |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả API của lớp `DigitalTwinManager` và `ConsistencyValidator`.
- **Provider Pattern details**: Interface cho phép nạp các rule mâu thuẫn động từ file cấu hình bên ngoài.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận tin -> khóa lock -> áp dụng update -> chạy so khớp chéo -> tính điểm -> phát hành mâu thuẫn (nếu có) -> lưu SQLite -> mở lock.
- **Migration Strategy & Testing Architecture**: Dùng kịch bản test giả lập nạp hàng loạt 10,000 tin update để kiểm tra hiệu năng lock.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_twin_dimensions.py` (Mapped to Task 1.1): Ghi và đọc đầy đủ dữ liệu 11 chiều, xác nhận khớp kiểu dữ liệu.
  - `tests/unit/test_consistency_rules.py` (Mapped to Task 1.3): Inject mâu thuẫn visual vs auth; kiểm tra phát hiện đúng sau < 10ms.
  - `tests/unit/test_staleness.py` (Mapped to Task 2.1): Giả lập ngừng phát sự kiện 30s; xác thực nhận được cảnh báo stale.
- **Integration Tests**:
  - `tests/integration/test_twin_persistence.py` (Mapped to Task 1.7): Khởi tạo, ghi dữ liệu, tắt ứng dụng, khôi phục lại từ SQLite và so khớp 100%.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% test đơn vị cho mâu thuẫn và cập nhật dữ liệu vượt qua.
  - [ ] Trạng thái được ghi nhận đầy đủ vào SQLite sau khi tắt phiên điều tra.
  - [ ] Điểm sức khỏe (health score) phản ánh chính xác số lượng lỗi tương thích.
- **Phase 2 Exit Criteria**:
  - [ ] Trình theo dõi stale phát hiện và cảnh báo chính xác dimension hết hạn mà không gây nghẽn luồng.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Khóa lock asyncio gây nghẽn luồng vĩnh viễn (deadlock) do tranh chấp ghi dữ liệu quá cao.
  - *Steps*: Thay thế khóa lock bằng cơ chế Single-Thread Queue processor cho các cập nhật, revert code `twin.py`.
  - *Recovery*: Đảm bảo trạng thái luôn nhất quán theo thứ tự gửi mà không bị treo.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Task 1.3 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.7 | Yes | No | No | No | No | Yes | Yes |
| Task 1.9 | Yes | Yes | Yes | Yes | Yes | No | No |
| Task 2.1 | Yes | Yes | Yes | No | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-060_vir_digital_twin_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/twin/stale_monitor.py

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích mô hình Digital Twin tiêu tốn ~5,000 tokens.
- **Parallel execution opportunities**: Thiết kế phần truy vấn và lịch sử buffer có thể triển khai song song.
- **Expected token savings**: Tiết kiệm ~30% tokens bằng cách kiểm thử kiểm tra mâu thuẫn chéo bằng các quy tắc logic thuần túy không chạy qua cơ sở dữ liệu SQLite thực.
- **Recommended execution strategy**: Hoàn thiện sớm bộ quy tắc kiểm tra chéo (consistency.py) trước khi viết cơ chế đồng bộ hóa đĩa.

---

## Recommended Next Skill
/blueprint
