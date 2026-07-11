<!-- File path: docs/plans/FEAT-059_vir_hearing_engine_and_touch_engine_plan.md -->

---
feature_id: FEAT-059
feature_name: Visual Intelligence Runtime — Hearing Engine & Touch Engine
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-059_vir_hearing_engine_and_touch_engine.md
next_artifact: ../designs/FEAT-059_vir_hearing_engine_and_touch_engine_blueprint.md
---

# FEAT-059: Visual Intelligence Runtime — Hearing Engine & Touch Engine

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Implement browser console log capture at all levels | [x] |
| FR-02 | Phase 1 | Task 1.2 | Capture JavaScript runtime exceptions and promise rejections | [x] |
| FR-03 | Phase 1 | Task 1.3 | Monitor all network transport requests (Fetch, XHR, GraphQL) | [x] |
| FR-04 | Phase 1 | Task 1.4 | Parse network payloads including HTTP headers and status codes | [x] |
| FR-05 | Phase 1 | Task 1.5 | Observe browser navigation and page load lifecycle events | [x] |
| FR-06 | Phase 1 | Task 1.6 | Capture Single Page Application (SPA) client router transitions | [x] |
| FR-13 | Phase 1 | Task 1.7 | Format and publish collected signals as Evidence on Event Bus | [x] |
| FR-14 | Phase 1 | Task 1.8 | Group correlated signals within temporal time windows | [x] |
| FR-15 | Phase 1 | Task 1.9 | Implement Touch Engine Mode A deterministic user actions | [x] |
| FR-21 | Phase 1 | Task 1.10| Detect dead clicks and interactions having zero visual effect | [x] |
| FR-07 | Phase 2 | Task 2.1 | Extract authentication token events and session timeouts | [x] |
| FR-08 | Phase 2 | Task 2.2 | Track framework state reactive mutations (React/Vue/Svelte) | [x] |
| FR-10 | Phase 2 | Task 2.3 | Listen to Web Vitals performance parameters (LCP, CLS, INP) | [x] |
| FR-11 | Phase 2 | Task 2.4 | Observe accessibility live regions and announcements | [x] |
| FR-16 | Phase 2 | Task 2.5 | Implement Touch Engine Mode B human behavior pointer emulation | [x] |
| FR-17 | Phase 2 | Task 2.6 | Manage seed numbers configuration for repeatable simulation | [x] |
| FR-18 | Phase 2 | Task 2.7 | Enforce deterministic-first interaction routing strategies | [x] |
| FR-20 | Phase 2 | Task 2.8 | Implement user action sequence recorder for debug replay | [x] |
| FR-09 | Phase 3 | Task 3.1 | Track background Service Workers installs and cache events | [x] |
| FR-12 | Phase 3 | Task 3.2 | Integrate media player audio playback monitors | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai lắng nghe luồng console của Browser.
- **Task 1.2**: [Coder] - Bắt lỗi JS ngoại lệ qua CDP page exception events.
- **Task 1.3**: [Coder] - Triển khai bộ chặn và lắng nghe network traffic.
- **Task 1.4**: [Coder] - Bóc tách header, status code và body (nếu cấu hình cho phép).
- **Task 1.5**: [Coder] - Lắng nghe các mốc tải trang (load, DOMContentLoaded).
- **Task 1.6**: [Coder] - Bắt các thay đổi url và lịch sử router của SPA.
- **Task 1.7**: [Coder] - Xuất bản các sự kiện nghe được thành đối tượng Evidence.
- **Task 1.8**: [Architect] - Thiết kế thuật toán nhóm sự kiện bằng correlation window (Observation Groups).
- **Task 1.9**: [Coder] - Triển khai điều hướng nhấp chuột, gõ phím chuẩn xác của Touch Mode A.
- **Task 1.10**: [Verifier] - Triển khai đo kiểm tra DOM/layout không thay đổi sau tương tác (Dead Clicks).
- **Task 2.1**: [Coder] - Lắng nghe các thay đổi cookie/localStorage để bắt sự kiện đăng nhập/đăng xuất.
- **Task 2.2**: [Coder] - Trích xuất lịch sử biến đổi state của framework tương ứng.
- **Task 2.3**: [Coder] - Thu thập chỉ số Web Vitals từ window performance APIs.
- **Task 2.4**: [Verifier] - Giám sát luồng thông báo ARIA và các cập nhật vai trò (roles).
- **Task 2.5**: [Architect] - Cài đặt thuật toán di chuyển chuột ngẫu nhiên, gõ phím trễ (imperfect path).
- **Task 2.6**: [Coder] - Đồng bộ hóa hạt giống ngẫu nhiên (random seeds) của Python cho Touch.
- **Task 2.7**: [Verifier] - Enforce luồng chạy luôn ưu tiên Mode A, chuyển Mode B khi tìm đường.
- **Task 2.8**: [Coder] - Xuất mảng hành động dạng JSON phục vụ tái lập lỗi (replay logs).
- **Task 3.1**: [Coder] - Lắng nghe Service Worker registration và cache storage updates.
- **Task 3.2**: [Coder] - Đo đạc trạng thái thẻ `<audio>` qua JavaScript hooks.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: [Task 1.1, Task 1.2, Task 1.3] -> Task 1.8 -> Task 1.9 -> Task 1.10
- **Parallel Tasks**: [Task 1.5, Task 1.6], [Task 2.1, Task 2.2, Task 2.3, Task 2.4], [Task 2.5, Task 2.6, Task 2.8]
- **Blocking Tasks**: Task 1.3 (blocks Task 1.4), Task 1.9 (blocks Task 1.10), Task 2.5 (blocks Task 2.7)
- **Independent Tasks**: Task 3.1, Task 3.2
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.8 (Hearing core event capturing & correlation)
  - **Group 2**: Task 1.5, Task 1.6, Task 1.7 (Browser state navigation tracking)
  - **Group 3**: Task 1.9, Task 1.10 (Touch Mode A deterministic execution)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3, Task 2.4 (Advanced runtime telemetry)
  - **Group 5**: Task 2.5, Task 2.6, Task 2.7, Task 2.8 (Human simulation exploratory touch loops)
  - **Group 6**: Task 3.1, Task 3.2 (Service workers and media tests)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/sensory/hearing/console.py` | Create | Lắng nghe console log |
| Task 1.2 | `vir_runtime/sensory/hearing/exceptions.py` | Create | Bắt lỗi runtime JS ngoại lệ |
| Task 1.3 | `vir_runtime/sensory/hearing/network.py` | Create | Đánh chặn network HTTP/WS traffic |
| Task 1.5 | `vir_runtime/sensory/hearing/lifecycle.py` | Create | Lắng nghe vòng đời tải trang |
| Task 1.6 | `vir_runtime/sensory/hearing/router.py` | Create | Lắng nghe định tuyến router của client |
| Task 1.8 | `vir_runtime/sensory/hearing/correlation.py`| Create | Ghép nhóm sự kiện cùng mã tương quan |
| Task 1.9 | `vir_runtime/sensory/touch/deterministic.py`| Create | Thực thi hành động chuột phím Mode A |
| Task 1.10| `vir_runtime/sensory/touch/dead_click.py` | Create | Phát hiện nhấp chuột chết (dead click) |
| Task 2.2 | `vir_runtime/sensory/hearing/state_observer.py`| Create | Thu hoạch state framework |
| Task 2.5 | `vir_runtime/sensory/touch/human_sim.py` | Create | Cài đặt di chuyển chuột dạng người |
| Task 2.8 | `vir_runtime/sensory/touch/recorder.py` | Create | Ghi nhận vết sự kiện để chạy lại (replay) |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Thiết kế các Interface `HearingEngine` và `TouchEngine`.
- **Provider Pattern details**: Định dạng tham số giao tiếp qua `BrowserAdapter` để thu thập console và gửi hành động chuột.
- **Data Flow / Sequence Flow**: Vẽ luồng khi gõ phím -> TouchEngine gửi lệnh -> HearingEngine ghi nhận network pending -> trang ổn định -> phản hồi.
- **Migration Strategy & Testing Architecture**: Viết các bài test giả lập sự kiện console và network để kiểm thử bộ gom nhóm correlation mà không mở Playwright.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_console_monitor.py` (Mapped to Task 1.1): Xác thực bắt log lỗi console chính xác.
  - `tests/unit/test_correlation_window.py` (Mapped to Task 1.8): Đảm bảo các sự kiện diễn ra trong 200ms được gộp chung nhóm.
  - `tests/unit/test_mouse_seed.py` (Mapped to Task 2.6): Đảm bảo hạt giống ngẫu nhiên tạo ra tọa độ di chuyển chuột giống hệt nhau.
- **Integration Tests**:
  - `tests/integration/test_dead_click_detector.py` (Mapped to Task 1.10): Kiểm chứng nhấp chuột vào phần tử không đổi layout/styles sinh ra lỗi dead_click.
  - `tests/integration/test_spa_router_events.py` (Mapped to Task 1.6): Xác nhận bắt đúng route chuyển tiếp dạng `/dashboard` -> `/settings`.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các cuộc gọi API, console error và exception được chuyển thành Evidence hợp lệ.
  - [ ] Nhấp chuột Mode A định hướng chuẩn xác phần tử đích.
  - [ ] Bộ lọc gom nhóm thời gian (correlation) hoạt động đúng như mong đợi.
- **Phase 2 Exit Criteria**:
  - [ ] Touch Mode B tạo ra chuỗi tương tác di chuyển chuột bất quy tắc có tính lặp lại (reproducible) qua seed.
  - [ ] Tệp tin log replay được kết xuất đúng cấu trúc JSON quy định.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Đánh chặn mạng (network interception) làm giảm băng thông và gây đứng nghẽn trình duyệt kiểm thử.
  - *Steps*: Revert cơ chế lắng nghe body mạng, chỉ lưu giữ URL và HTTP Status.
  - *Recovery*: Đảm bảo trình duyệt chạy ổn định với tốc độ tải trang bình thường.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.3 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.8 | Yes | Yes | Yes | No | No | Yes | Yes |
| Task 1.9 | Yes | Yes | Yes | No | No | No | No |
| Task 2.5 | Yes | Yes | Yes | Yes | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-059_vir_hearing_touch_engines_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/sensory/touch/human_sim.py
- **Phase 3 Artifacts**: vir_runtime/sensory/hearing/state_observer.py

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch hearing/touch tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Thiết kế phần ghi nhận replay (Task 2.8) và lắng nghe Web Vitals (Task 2.3) có thể tiến hành song song.
- **Expected token savings**: Tiết kiệm ~40% tokens bằng cách viết mock mạng để kiểm thử router listener không cần mở web.
- **Recommended execution strategy**: Hoàn thiện phần đánh chặn mạng (network.py) và click chuột (deterministic.py) trước khi mở rộng ra mô phỏng con người.

---

## Recommended Next Skill
/blueprint
