<!-- File path: docs/plans/FEAT-064_vir_memory_learning_plan.md -->

---
feature_id: FEAT-064
feature_name: Visual Intelligence Runtime — Memory Architecture & Continuous Learning
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-064_vir_memory_architecture_and_continuous_learning.md
next_artifact: ../designs/FEAT-064_vir_memory_learning_blueprint.md
---

# FEAT-064: Visual Intelligence Runtime — Memory Architecture & Continuous Learning

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Establish hybrid storage (filesystem, SQLite, Qdrant) | [x] |
| FR-02 | Phase 1 | Task 1.2 | Create baseline, current, and diff visual folders structures | [x] |
| FR-03 | Phase 1 | Task 1.3 | Store runs metadata in SQLite tables | [x] |
| FR-04 | Phase 1 | Task 1.4 | Setup vector metadata mappings for Qdrant search keys | [x] |
| FR-05 | Phase 1 | Task 1.5 | Restrict Qdrant storage to embeddings and text keys only | [x] |
| FR-06 | Phase 1 | Task 1.6 | Implement Short-term Memory asyncio dict | [x] |
| FR-07 | Phase 1 | Task 1.7 | Implement Working Memory asyncio dict | [x] |
| FR-08 | Phase 1 | Task 1.8 | Implement SQLite-backed Long-term Memory for agents | [x] |
| FR-09 | Phase 1 | Task 1.9 | Setup event bus streaming listener for Shared Memory | [x] |
| FR-10 | Phase 1 | Task 1.10| Build query API connector to Knowledge Runtime | [x] |
| FR-11 | Phase 1 | Task 1.11| Store and version visual baselines | [x] |
| FR-12 | Phase 1 | Task 1.13| Classify regression states (NO_CHANGE, VISUAL_REGRESSION) | [x] |
| FR-13 | Phase 1 | Task 1.14| Generate deterministic DOM structure signature hashes | [x] |
| FR-14 | Phase 1 | Task 1.15| Enforce human approval gates for diff changes > 30% | [x] |
| FR-15 | Phase 1 | Task 1.16| Publish visual regression findings as Evidence objects | [x] |
| FR-16 | Phase 1 | Task 1.17| Log regression histories per feature per commit in SQLite | [x] |
| FR-21 | Phase 1 | Task 1.18| Query long-term memory for past issues before generating hypotheses | [x] |
| FR-17 | Phase 2 | Task 2.1 | Extract `LearningOutcome` attributes on investigation close | [x] |
| FR-18 | Phase 2 | Task 2.2 | Store embedded lessons inside Qdrant collection | [x] |
| FR-19 | Phase 2 | Task 2.3 | Promote validated high-confidence outcomes to Knowledge Runtime | [x] |
| FR-20 | Phase 2 | Task 2.4 | Export memories snapshots to project vault Obsidian folders | [x] |
| FR-22 | Phase 2 | Task 2.5 | Boost agent authority weight after successful memory resolution | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Thiết kế cấu trúc lưu trữ hỗn hợp (hybrid storage) và phân bổ tệp.
- **Task 1.2**: [Coder] - Tạo cây thư mục trống trong `.agents/visual-runtime/artifacts/`.
- **Task 1.3**: [Coder] - Thiết lập cấu trúc cơ sở dữ liệu SQLite lưu metadata.
- **Task 1.4**: [Coder] - Cấu hình Qdrant collection và vector schema.
- **Task 1.5**: [Verifier] - Triển khai bộ chặn kiểm tra đầu vào Qdrant để đảm bảo không lưu ảnh thô.
- **Task 1.6**: [Coder] - Viết luồng nạp và giải phóng bộ đệm ngắn hạn (Short-term).
- **Task 1.7**: [Coder] - Viết luồng nạp và giải phóng bộ đệm làm việc (Working).
- **Task 1.8**: [Coder] - Viết luồng đồng bộ bộ nhớ dài hạn (Long-term) của agent vào SQLite.
- **Task 1.9**: [Coder] - Tạo listener đăng ký sự kiện evidence chia sẻ dạng Shared Memory.
- **Task 1.10**: [Architect] - Xây dựng cầu nối SDK gọi sang API của Knowledge Runtime.
- **Task 1.11**: [Coder] - Triển khai lập chỉ mục tệp ảnh baselines theo feature, route, commit.
- **Task 1.13**: [Verifier] - Phân nhóm các mức độ sai khác pixel thành các nhãn hồi quy (regression).
- **Task 1.14**: [Architect] - Thuật toán băm cấu trúc DOM (DOM fingerprinting) làm khóa đệm.
- **Task 1.15**: [Runtime] - Tích hợp approval gate yêu cầu người dùng xác nhận nạp baseline mới nếu sai lệch > 30%.
- **Task 1.16**: [Coder] - Đóng gói kết quả regression thành Evidence đẩy lên bus.
- **Task 1.17**: [Coder] - Ghi nhận lịch sử hồi quy vào bảng SQLite.
- **Task 1.18**: [Verifier] - Điều hướng Coder/RCA truy vấn tri thức cũ trước khi suy đoán (Hypothesize).
- **Task 2.1**: [Architect] - Thiết kế Dataclass `LearningOutcome`.
- **Task 2.2**: [Coder] - Viết trình sinh vector embeddings và lưu trữ vào Qdrant.
- **Task 2.3**: [Verifier] - Chặn đề xuất bài học nếu điểm tin cậy tổng hợp của phiên < 0.8.
- **Task 2.4**: [Documentation] - Viết hàm xuất bản ghi nhớ sang tệp tin Markdown của Obsidian vault.
- **Task 2.5**: [Verifier] - Tăng trọng số bỏ phiếu của agent trong `vir_agents.yaml` và log audit.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 1.11 -> Task 1.15
- **Parallel Tasks**: [Task 1.4, Task 1.5], [Task 1.6, Task 1.7, Task 1.8, Task 1.9, Task 1.10], [Task 1.13, Task 1.14, Task 1.16, Task 1.17], [Task 2.1, Task 2.2, Task 2.5]
- **Blocking Tasks**: Task 1.11 (blocks Task 1.15), Task 1.4 (blocks Task 2.2)
- **Independent Tasks**: Task 1.18, Task 2.4
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.11, Task 1.15 (Visual baseline filesystem structures)
  - **Group 2**: Task 1.4, Task 1.5, Task 2.2 (Qdrant semantic vector memory configurations)
  - **Group 3**: Task 1.6, Task 1.7, Task 1.8, Task 1.9, Task 1.10 (5-layer agent memory execution context)
  - **Group 4**: Task 1.13, Task 1.14, Task 1.16, Task 1.17, Task 1.18 (Regression Engine algorithms)
  - **Group 5**: Task 2.1, Task 2.3, Task 2.4, Task 2.5 (Continuous learning feedback loops)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/memory/adapter.py` | Create | Lớp cơ sở trừu tượng hóa các adapter lưu trữ |
| Task 1.3 | `vir_runtime/memory/sqlite_db.py` | Create | Quản lý bảng SQLite ghi nhận vết |
| Task 1.4 | `vir_runtime/memory/qdrant_db.py` | Create | Kết nối và nạp vector Qdrant |
| Task 1.8 | `vir_runtime/memory/agent_memory.py` | Create | Triển khai Long-term memory của agent |
| Task 1.11| `vir_runtime/memory/baselines.py` | Create | Quản lý ảnh baselines và phiên bản |
| Task 1.14| `vir_runtime/memory/fingerprint.py` | Create | Thuật toán băm chữ ký DOM |
| Task 2.1 | `vir_runtime/memory/learning.py` | Create | Triển khai LearningOutcome và Obsidian export |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của `MemoryAdapter`, `BaselineManager`, và `LearningEngine`.
- **Provider Pattern details**: Interface cho phép nạp các adapter embeddings (như OpenAI hay Ollama local) che giấu cài đặt kết nối.
- **Data Flow / Sequence Flow**: Vẽ luồng khi kết thúc điều tra -> tạo LearningOutcome -> sinh embedding -> nạp Qdrant -> ghi SQLite -> xuất Obsidian -> cập nhật trọng số.
- **Migration Strategy & Testing Architecture**: Sử dụng các MockQdrantClient để chạy test unit tốc độ cao không phụ thuộc kết nối mạng.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_dom_fingerprint.py` (Mapped to Task 1.14): Đảm bảo DOM giống nhau sinh mã băm bằng nhau, thay đổi 1 thẻ HTML sinh mã băm khác.
  - `tests/unit/test_baseline_versions.py` (Mapped to Task 1.11): Xác thực lưu và lấy baselines đúng theo commit hash.
  - `tests/unit/test_memory_hypothesis.py` (Mapped to Task 1.18): Đảm bảo hệ thống nạp bài học cũ trước khi lập danh sách giả thuyết.
- **Integration Tests**:
  - `tests/integration/test_baseline_veto_gate.py` (Mapped to Task 1.15): Thử nghiệm nạp ảnh sai biệt 40% mà không có con người duyệt; đảm bảo bị chặn.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các chỉ số baselines và regression ghi nhận thành công.
  - [ ] Hồi quy sai biệt lớn (> 30%) bị chặn và kích hoạt approval gate.
  - [ ] DOM fingerprinting đạt độ nhạy phân tách cao.
- **Phase 2 Exit Criteria**:
  - [ ] Học hỏi tri thức (learning outcome) lưu thành công vào cơ sở dữ liệu vector.
  - [ ] Trọng số của các agent hỗ trợ tìm ra lỗi được cập nhật chính xác.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Kết nối Qdrant hoặc sinh embeddings bị chậm trễ gây treo CI.
  - *Steps*: Tạm thời tắt bộ nhớ ngữ nghĩa Qdrant, chuyển sang lưu vết SQLite metadata thuần túy, revert code `qdrant_db.py`.
  - *Recovery*: Đảm bảo hệ thống hoạt động ổn định và bỏ qua việc học hỏi ngữ nghĩa.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Task 1.4 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.11| Yes | No | Yes | Yes | No | Yes | Yes |
| Task 1.15| Yes | Yes | Yes | No | Yes | Yes | No |
| Task 2.1 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-064_vir_memory_learning_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/memory/learning.py
- **Phase 3 Artifacts**: docs/adr/ADR-018_memory_vector_indexes.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch bộ nhớ/học hỏi tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Viết cấu trúc fingerprint và nạp SQLite (Task 1.3, 1.14) song song với qdrant_db.py.
- **Expected token savings**: Tiết kiệm ~40% tokens nhờ chạy các kiểm thử embeddings trên mô hình MockClient RAM không cần kết nối mạng internet.
- **Recommended execution strategy**: Hoàn thành sớm phần SQLite đồng bộ (sqlite_db.py) và baselines.py trước khi xây dựng học hỏi liên tục.

---

## Recommended Next Skill
/blueprint
