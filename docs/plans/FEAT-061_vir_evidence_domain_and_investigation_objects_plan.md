<!-- File path: docs/plans/FEAT-061_vir_evidence_domain_and_investigation_objects_plan.md -->

---
feature_id: FEAT-061
feature_name: Visual Intelligence Runtime — Evidence Domain & Investigation Objects
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-061_vir_evidence_domain_and_investigation_objects.md
next_artifact: ../designs/FEAT-061_vir_evidence_domain_and_investigation_objects_blueprint.md
---

# FEAT-061: Visual Intelligence Runtime — Evidence Domain & Investigation Objects

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Model core Evidence domain dataclass properties and metadata fields | [x] |
| FR-02 | Phase 1 | Task 1.2 | Define classification mappings for visual, network, and performance data | [x] |
| FR-03 | Phase 1 | Task 1.3 | Enforce strict immutability checks on Evidence instances | [x] |
| FR-04 | Phase 1 | Task 1.4 | Map relationship networks (supports, contradicts, supersedes) | [x] |
| FR-06 | Phase 1 | Task 1.5 | Create Evidence Query API supporting criteria filters | [x] |
| FR-07 | Phase 1 | Task 1.6 | Create Evidence Engine aggregating streaming bus events | [x] |
| FR-08 | Phase 1 | Task 1.7 | Detect and publish `evidence.contradiction` conflict signals | [x] |
| FR-10 | Phase 1 | Task 1.8 | Model Investigation lifecycle attributes and symptoms fields | [x] |
| FR-11 | Phase 1 | Task 1.9 | Establish cross-session SQLite persistence for active Investigations | [x] |
| FR-12 | Phase 1 | Task 1.10| Build Investigation status state transition handlers | [x] |
| FR-14 | Phase 1 | Task 1.11| Build confidence score calculator from linked evidence arrays | [x] |
| FR-15 | Phase 1 | Task 1.12| Create tested/rejected Hypothesis mapping matrices | [x] |
| FR-16 | Phase 1 | Task 1.13| Enforce multi-evidence validator rules for root cause confirmation | [x] |
| FR-17 | Phase 1 | Task 1.14| Ensure diagnostic outputs reference explicit Evidence IDs | [x] |
| FR-19 | Phase 1 | Task 1.15| Generate dynamic chronological Evidence Timelines | [x] |
| FR-20 | Phase 1 | Task 1.16| Aggregate lifecycle updates into Investigation Timelines | [x] |
| FR-21 | Phase 1 | Task 1.17| Explicitly correlate logs, network errors, and visual elements | [x] |
| FR-05 | Phase 2 | Task 2.1 | Implement auto-transition transitions for stale evidence | [x] |
| FR-09 | Phase 2 | Task 2.2 | Group correlated evidence arrays into logical Observation Groups | [x] |
| FR-13 | Phase 2 | Task 2.3 | Support child Investigation spawn pipelines | [x] |
| FR-18 | Phase 2 | Task 2.4 | Export validated lessons outputs to Memory Engines | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Định nghĩa cấu trúc Python Dataclass của đối tượng Evidence.
- **Task 1.2**: [Coder] - Cài đặt phân loại kiểu dữ liệu enum cho các nguồn evidence.
- **Task 1.3**: [Verifier] - Triển khai bộ bảo vệ đóng băng (frozen=True) ngăn chặn chỉnh sửa thuộc tính.
- **Task 1.4**: [Architect] - Xây dựng sơ đồ liên kết đồ thị giữa các tệp tin evidence.
- **Task 1.5**: [Coder] - Viết trình xử lý truy vấn dựa trên các bộ lọc (agent, severity, timestamp).
- **Task 1.6**: [Coder] - Triển khai lõi Evidence Engine lắng nghe và lưu trữ tin đến.
- **Task 1.7**: [Verifier] - Cài đặt thuật toán đối chiếu dữ liệu phát hiện mâu thuẫn tức thời.
- **Task 1.8**: [Architect] - Thiết lập cấu trúc dữ liệu đối tượng Investigation và lưu trữ tiến trình.
- **Task 1.9**: [Coder] - Thiết lập bảng `vir_evidence` và `vir_investigations` trong SQLite.
- **Task 1.10**: [Coder] - Viết máy trạng thái (state machine) chuyển đổi các bước điều tra.
- **Task 1.11**: [Verifier] - Xây dựng thuật toán tính toán độ tin cậy kết hợp (aggregate confidence).
- **Task 1.12**: [Coder] - Triển khai lớp lưu trữ giả thuyết (Hypothesis) kèm lý do bác bỏ.
- **Task 1.13**: [Verifier] - Enforce quy tắc chặn kết luận nguyên nhân nếu chỉ có 1 bằng chứng hỗ trợ.
- **Task 1.14**: [Documentation] - Định dạng đầu ra báo cáo chi tiết đính kèm mã UUID của bằng chứng.
- **Task 1.15**: [Coder] - Sắp xếp và kết xuất danh sách timeline sự kiện dạng biểu đồ/JSON.
- **Task 1.16**: [Coder] - Lưu vết lịch sử thay đổi trạng thái của phiên điều tra.
- **Task 1.17**: [Architect] - Viết bộ liên kết ánh xạ console/network error sang node DOM visual tương ứng.
- **Task 2.1**: [Coder] - Viết logic tự động dọn dẹp chuyển trạng thái bằng chứng sau khi đóng phiên.
- **Task 2.2**: [Architect] - Nhóm các evidence xảy ra cùng thời điểm và cùng đối tượng DOM.
- **Task 2.3**: [Coder] - Hỗ trợ phân rã bài toán lớn thành các sub-investigations độc lập.
- **Task 2.4**: [Coder] - Viết hàm xuất bản các bài học kinh nghiệm (learning outcome) sang bus.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.6 -> Task 1.7 -> Task 1.17
- **Parallel Tasks**: [Task 1.2, Task 1.3, Task 1.4], [Task 1.8, Task 1.10, Task 1.12], [Task 1.15, Task 1.16]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.6), Task 1.8 (blocks Task 1.9), Task 1.6 (blocks Task 1.13)
- **Independent Tasks**: Task 1.5, Task 2.4
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.6 (Core Evidence domain structures)
  - **Group 2**: Task 1.7, Task 1.17, Task 2.2 (Contradiction mapping & diagnostics)
  - **Group 3**: Task 1.8, Task 1.9, Task 1.10, Task 1.12 (Investigation session lifecycles)
  - **Group 4**: Task 1.11, Task 1.13, Task 1.14 (Validation safety verification checkers)
  - **Group 5**: Task 1.5, Task 1.15, Task 1.16 (Query and timeline builders)
  - **Group 6**: Task 2.1, Task 2.3, Task 2.4 (Memory and child sandbox cleanups)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/domain/evidence.py` | Create | Định nghĩa lớp Dataclass và kiểu dữ liệu Evidence |
| Task 1.6 | `vir_runtime/domain/evidence_engine.py`| Create | Lõi gom nhận và lưu trữ evidence |
| Task 1.8 | `vir_runtime/domain/investigation.py` | Create | Mô tả cấu trúc và vòng đời Investigation |
| Task 1.9 | `vir_runtime/domain/db_schema.sql` | Create | Khai báo cấu trúc bảng SQLite |
| Task 1.11| `vir_runtime/domain/confidence.py` | Create | Hàm tính điểm tin cậy tổng hợp |
| Task 1.15| `vir_runtime/domain/timeline.py` | Create | Xây dựng timeline biểu đồ |
| Task 1.17| `vir_runtime/domain/correlator.py` | Create | Ánh xạ lỗi console/mạng sang visual DOM node |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả API của `EvidenceEngine` và `InvestigationManager`.
- **Provider Pattern details**: Interface cho phép nạp các cơ chế lưu trữ (như JSON file hay Postgres trong tương lai) qua Storage Adapter.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận tin -> lưu SQLite `vir_evidence` -> cập nhật danh sách link -> so sánh phát hiện mâu thuẫn -> gắn tag mâu thuẫn -> cập nhật tiến trình điều tra.
- **Migration Strategy & Testing Architecture**: Sử dụng các file mock SQLite trong bộ nhớ RAM (`:memory:`) để chạy test unit tốc độ cao.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_evidence_immutability.py` (Mapped to Task 1.3): Đảm bảo raises lỗi khi gán đè thuộc tính của Evidence.
  - `tests/unit/test_confidence_calculator.py` (Mapped to Task 1.11): Kiểm tra công thức gom 2 evidence 0.8 và 0.9 ra điểm chính xác.
  - `tests/unit/test_correlator.py` (Mapped to Task 1.17): Xác thực kết nối đúng lỗi API fail với element click tương ứng.
- **Integration Tests**:
  - `tests/integration/test_investigation_lifecycle.py` (Mapped to Task 1.10): Đảm bảo các bước chuyển trạng thái OPEN -> INVESTIGATING -> CONCLUDED khớp quy tắc máy trạng thái.
  - `tests/integration/test_root_cause_gate.py` (Mapped to Task 1.13): Đảm bảo ném lỗi từ chối kết luận nguyên nhân nếu chỉ liên kết 1 bằng chứng.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các bằng chứng được ghi nhận thành công vào SQLite dưới dạng bất biến.
  - [ ] Bộ lọc tương quan liên kết thành công lỗi mạng và DOM element tương ứng.
  - [ ] Không thể kết luận nguyên nhân gốc nếu thiếu số lượng bằng chứng hỗ trợ tối thiểu (2).
- **Phase 2 Exit Criteria**:
  - [ ] Trình spawn sub-investigations phân rã chính xác ngữ cảnh không bị rò rỉ phiên.
  - [ ] Dữ liệu kết xuất bài học (learning outcomes) gửi lên bus hợp lệ.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Ghi dữ liệu SQLite đồng thời quá lớn gây lỗi khóa cơ sở dữ liệu (database locked).
  - *Steps*: Kích hoạt chế độ SQLite WAL mode, khôi phục tệp cấu hình db.
  - *Recovery*: Đảm bảo các tiến trình ghi chạy tuần tự qua hàng đợi ghi đơn luồng.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | No | No | No | Yes | No |
| Task 1.6 | Yes | Yes | Yes | Yes | No | Yes | Yes |
| Task 1.9 | Yes | No | No | No | No | Yes | Yes |
| Task 1.13| Yes | Yes | Yes | No | Yes | No | No |
| Task 1.15| Yes | No | Yes | Yes | Yes | Yes | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-061_vir_evidence_investigation_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/domain/timeline.py
- **Phase 3 Artifacts**: docs/adr/ADR-011_evidence_persistence.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích thực thể Bằng chứng tốn ~5,500 tokens.
- **Parallel execution opportunities**: Thiết kế phần Hypothesis lưu trữ và Timeline biểu đồ có thể làm song song.
- **Expected token savings**: Tiết kiệm ~40% tokens bằng cách chạy kiểm thử cơ sở dữ liệu trên bộ nhớ đệm RAM (`:memory:`) không ghi xuống đĩa trong quá trình phát triển của Coder.
- **Recommended execution strategy**: Hoàn thành sớm cấu trúc cơ sở dữ liệu SQL trước khi bắt tay viết logic tìm mâu thuẫn.

---

## Recommended Next Skill
/blueprint
