<!-- File path: docs/plans/FEAT-072_vir_goal_explorer_and_action_planner_plan.md -->

---
feature_id: FEAT-072
feature_name: Visual Intelligence Runtime — Goal Explorer & Action Planner
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-072_vir_goal_explorer_and_action_planner.md
next_artifact: ../designs/FEAT-072_vir_goal_explorer_and_action_planner_blueprint.md
---

# FEAT-072: Visual Intelligence Runtime — Goal Explorer & Action Planner

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Parse specification target states and preconditions | [x] |
| FR-03 | Phase 1 | Task 1.2 | Model State Transition Graph structure and DOM hashes | [x] |
| FR-04 | Phase 1 | Task 1.3 | Implement path-finding algorithms (A* or Dijkstra) | [x] |
| FR-06 | Phase 1 | Task 1.4 | Classify Touch actions into SAFE vs UNSAFE categories | [x] |
| FR-07 | Phase 1 | Task 1.5 | Intercept and block destructive actions unless authorized | [x] |
| FR-09 | Phase 1 | Task 1.6 | Execute backtracking recovery to last healthy state | [x] |
| FR-10 | Phase 1 | Task 1.7 | Enforce session limits (max duration, max clicks/steps) | [x] |
| FR-11 | Phase 1 | Task 1.8 | Detect cyclic loop sequences and halt exploration | [x] |
| FR-14 | Phase 1 | Task 1.9 | Re-run identical paths using recorded action seed logs | [x] |
| FR-17 | Phase 1 | Task 1.10| Export planned action sequences arrays to Touch Engine | [x] |
| FR-18 | Phase 1 | Task 1.11| Request human confirmation gate before destructive actions | [x] |
| FR-02 | Phase 2 | Task 2.1 | Extract multi-hop user-journey graphs automatically | [x] |
| FR-05 | Phase 2 | Task 2.2 | Build auto-fill input forms with dummy data arrays | [x] |
| FR-08 | Phase 2 | Task 2.3 | Apply user role boundary restrictions checklist | [x] |
| FR-12 | Phase 2 | Task 2.4 | Implement detour routing to bypass blocked paths | [x] |
| FR-13 | Phase 2 | Task 2.5 | Coordinate imperfect human timings parameters in plans | [x] |
| FR-15 | Phase 2 | Task 2.6 | Calculate target exploration coverage percentages | [x] |
| FR-16 | Phase 2 | Task 2.7 | Publish `goal.unreachable` event if target state fails | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Viết trình phân tích tệp tin YAML đặc tả kịch bản kiểm thử.
- **Task 1.2**: [Architect] - Thiết lập cấu trúc dữ liệu đồ thị chuyển trạng thái (State Transition Graph).
- **Task 1.3**: [Coder] - Triển khai thuật toán tìm đường Dijkstra/A* tìm chuỗi click tối ưu.
- **Task 1.4**: [Architect] - Phân nhóm các hành động an toàn và nguy hại (mutates/deletes).
- **Task 1.5**: [Verifier] - Triển khai bộ chặn (security filter) các hành động nguy hại ngoài ý muốn.
- **Task 1.6**: [Coder] - Triển khai cơ chế khôi phục trạng thái cũ (backtrack) qua Sandbox.
- **Task 1.7**: [Verifier] - Cài đặt bộ giám sát thời lượng và bước chạy tối đa (limit budgets).
- **Task 1.8**: [Verifier] - Thiết lập bộ phát hiện đi vòng tròn (loop detector) và ngắt khẩn cấp.
- **Task 1.9**: [Coder] - Viết bộ khôi phục chuỗi thao tác từ tệp tin log replay.
- **Task 1.10**: [Coder] - Thiết lập hàm chuyển đổi graph steps thành tập hợp lệnh cho Touch Engine.
- **Task 1.11**: [Runtime] - Bổ sung cổng chờ con người phê duyệt (approval gate) trước lệnh destructive.
- **Task 2.1**: [Architect] - Xây dựng sơ đồ phân tích hành trình người dùng (User Journeys).
- **Task 2.2**: [Coder] - Viết bộ sinh dữ liệu điền form (form auto-filler) ngẫu nhiên.
- **Task 2.3**: [Verifier] - Thiết lập rào cản phân quyền phân phối vai trò kiểm thử.
- **Task 2.4**: [Coder] - Tích hợp giải pháp tính toán đường vòng thay thế (detour) khi gặp nút nghẽn.
- **Task 2.5**: [Architect] - Đồng bộ hóa Mouse timing ngẫu nhiên từ Touch Engine.
- **Task 2.6**: [Coder] - Tính toán điểm số phủ DOM và chỉ tiêu spec đã ghé thăm.
- **Task 2.7**: [Coder] - Phát hành sự kiện khi không tìm ra đường đi đến trạng thái đích.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.2 -> Task 1.3 -> Task 1.6 -> Task 1.8 -> Task 1.10
- **Parallel Tasks**: [Task 1.1, Task 1.4, Task 1.5], [Task 1.7, Task 1.9, Task 1.11], [Task 2.2, Task 2.3, Task 2.6], [Task 2.4, Task 2.5, Task 2.7]
- **Blocking Tasks**: Task 1.2 (blocks Task 1.3), Task 1.3 (blocks Task 1.10), Task 2.4 (blocks Task 2.7)
- **Independent Tasks**: Task 1.11, Task 2.6
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.2, Task 1.3, Task 1.6, Task 1.8, Task 1.10 (Pathfinding and Graph traversal pipeline)
  - **Group 2**: Task 1.1, Task 1.4, Task 1.5, Task 1.7 (Safety limits and security checks)
  - **Group 3**: Task 1.9, Task 1.11, Task 2.2 (Replay, human approvals, and dynamic form fillers)
  - **Group 4**: Task 2.1, Task 2.3, Task 2.4, Task 2.5, Task 2.6, Task 2.7 (Advanced detours, coverage metrics & reporting)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/planner/spec_parser.py` | Create | Trình phân tích spec đầu vào |
| Task 1.2 | `vir_runtime/planner/graph.py` | Create | Quản lý đồ thị trạng thái STG |
| Task 1.3 | `vir_runtime/planner/pathfinder.py` | Create | Thuật toán tìm đường đi A* |
| Task 1.5 | `vir_runtime/planner/security.py` | Create | Bộ lọc an toàn chặn các lệnh UNSAFE |
| Task 1.8 | `vir_runtime/planner/loop.py` | Create | Trình giám sát phát hiện lặp vòng tròn |
| Task 1.10| `vir_runtime/planner/bridge.py` | Create | Chuyển đổi graph steps sang lệnh Touch Engine |
| Task 2.2 | `vir_runtime/planner/forms.py` | Create | Điền dữ liệu giả vào các input forms |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của `spec_parser`, `STGGraph`, `Pathfinder`, và `ActionSafetyChecker`.
- **Provider Pattern details**: Interface cho phép nạp các chính sách an toàn từ tệp cấu hình safety.yaml.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận mục tiêu kiểm thử -> đọc spec -> chạy A* tìm chuỗi click -> kiểm tra tính an toàn từng click -> gửi Touch Engine -> nếu gãy -> backtrack quay lại nút cũ.
- **Migration Strategy & Testing Architecture**: Viết test unit cho thuật toán tìm đường trên đồ thị cấu trúc 20 nodes giả lập trong RAM mà không cần mở trình duyệt.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_pathfinder.py` (Mapped to Task 1.3): Đảm bảo tìm đường đi ngắn nhất chính xác giữa 5 layouts.
  - `tests/unit/test_action_safety.py` (Mapped to Task 1.5): Xác thực chặn và hỏi ý kiến người dùng khi gặp click có selector delete.
  - `tests/unit/test_loop_halt.py` (Mapped to Task 1.8): Giả lập nhấp chuột tuần hoàn qua lại giữa trang A và B; kiểm tra hệ thống dừng sau đúng 4 chu kỳ.
- **Integration Tests**:
  - `tests/integration/test_backtrack.py` (Mapped to Task 1.6): Thử điều hướng đến trang lỗi 500, xác nhận kích hoạt backtrack thành công quay lại nút STG ổn định gần nhất.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Tìm đường đi A* trên đồ thị 50 nodes hoàn tất trong < 100ms.
  - [ ] Chặn thành công các click UNSAFE ngoài luồng phê duyệt.
  - [ ] Nhận diện và thoát khỏi vòng lặp vô hạn (infinite loop) thành công.
- **Phase 2 Exit Criteria**:
  - [ ] Sinh dữ liệu form điền chính xác cho các thẻ input, select.
  - [ ] Tạo đường vòng (detour) thành công khi gặp nút bị chặn.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Thuật toán tìm đường tính sai gây lặp vô hạn hoặc kẹt cứng trình duyệt không thể điều hướng tiếp.
  - *Steps*: Revert cơ chế Dijkstra, gán cứng chuỗi điều hướng click tuần tự (hardcoded path) cho kịch bản, khôi phục code `graph.py`.
  - *Recovery*: Đảm bảo kiểm thử chạy thông mà không bị tắc nghẽn bởi logic STG.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.2 | Yes | Yes | Yes | Yes | No | Yes | Yes |
| Task 1.3 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.5 | Yes | Yes | Yes | No | Yes | No | No |
| Task 1.8 | Yes | No | Yes | No | No | Yes | No |
| Task 2.2 | Yes | No | Yes | No | No | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-072_vir_goal_planner_blueprint.md
- **Phase 2 Artifacts**: .agents/visual-runtime/config/safety.yaml
- **Phase 3 Artifacts**: docs/adr/ADR-016_pathfinding_navigation.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch Goal planner tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm viết spec_parser và safety check có thể chạy song song với lõi pathfinder.
- **Expected token savings**: Tiết kiệm ~40% tokens bằng cách viết test unit chạy thuật toán tìm đường trên mạng lưới nút giả lập trong RAM không mở Playwright.
- **Recommended execution strategy**: Hoàn thành sớm thuật toán tìm đường (pathfinder.py) và graph.py trước khi phát triển bộ điền form tự động.

---

## Recommended Next Skill
/blueprint
