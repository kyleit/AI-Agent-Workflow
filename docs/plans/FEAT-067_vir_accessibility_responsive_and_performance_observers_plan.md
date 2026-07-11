<!-- File path: docs/plans/FEAT-067_vir_accessibility_responsive_and_performance_observers_plan.md -->

---
feature_id: FEAT-067
feature_name: Visual Intelligence Runtime — Accessibility, Responsive & Performance Observers
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-067_vir_accessibility_responsive_and_performance_observers.md
next_artifact: ../designs/FEAT-067_vir_accessibility_responsive_and_performance_observers_blueprint.md
---

# FEAT-067: Visual Intelligence Runtime — Accessibility, Responsive & Performance Observers

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Integrate WCAG 2.1 AA compliance audit validation checks | [x] |
| FR-02 | Phase 1 | Task 1.2 | Implement check rules (focus, role attributes, alt labels) | [x] |
| FR-03 | Phase 1 | Task 1.3 | Query computed style DOM maps from Vision Layer 1 and contrast | [x] |
| FR-04 | Phase 1 | Task 1.4 | Enable VETO gates blocking PASS on key accessibility trap states | [x] |
| FR-05 | Phase 1 | Task 1.5 | Model custom project WCAG rules configurations loaders | [x] |
| FR-06 | Phase 1 | Task 1.6 | Output structured `AccessibilityFinding` objects to Event Bus | [x] |
| FR-07 | Phase 1 | Task 1.7 | Configure responsive verification breakpoint widths | [x] |
| FR-08 | Phase 1 | Task 1.8 | Audit viewport sizes checking overlap, scrolling, readability | [x] |
| FR-09 | Phase 1 | Task 1.9 | Detect layout collapses and fixed-width element leaks | [x] |
| FR-10 | Phase 1 | Task 1.10| Output structured `ResponsiveFinding` objects to Event Bus | [x] |
| FR-12 | Phase 1 | Task 1.11| Capture Web Vitals metrics (LCP, CLS, TTFB, INP) | [x] |
| FR-13 | Phase 1 | Task 1.12| Load performance quality boundary thresholds from overrides | [x] |
| FR-14 | Phase 1 | Task 1.13| Identify specific DOM elements triggering layout shifts (CLS) | [x] |
| FR-16 | Phase 1 | Task 1.14| Output structured `PerformanceFinding` objects to Event Bus | [x] |
| FR-11 | Phase 2 | Task 2.1 | Integrate responsive design rules checks with Design Authority | [x] |
| FR-15 | Phase 2 | Task 2.2 | Build frame rate (FPS) tracker assessing animation janks | [x] |
| FR-17 | Phase 2 | Task 2.3 | Connect performance POOR scoring weights to Consensus votes | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Tích hợp thư viện quét tuân thủ WCAG (Playwright A11y / axe-core).
- **Task 1.2**: [Coder] - Triển khai bộ phân tích thẻ focus, vai trò ARIA và sự hiện diện của alt text.
- **Task 1.3**: [Coder] - Lấy các thuộc tính màu sắc từ Vision Layer 1 để kiểm tra tương phản tự động.
- **Task 1.4**: [Verifier] - Triển khai cổng VETO phủ quyết của Accessibility Engine khi phát hiện lỗi nghiêm trọng.
- **Task 1.5**: [Coder] - Thiết lập cấu trúc cấu hình mức độ WCAG (AA vs AAA) từ `vir_observers.yaml`.
- **Task 1.6**: [Architect] - Khai báo cấu trúc đối tượng `AccessibilityFinding`.
- **Task 1.7**: [Coder] - Viết trình thay đổi viewport trình duyệt kiểm tra breakpoint.
- **Task 1.8**: [Verifier] - Xây dựng bộ quét phần tử chồng lấp (element overlap) bằng bounding boxes.
- **Task 1.9**: [Coder] - Phát hiện sự tồn tại của thanh cuộn ngang vi phạm responsive.
- **Task 1.10**: [Architect] - Khai báo cấu trúc đối tượng `ResponsiveFinding`.
- **Task 1.11**: [Coder] - Đo đạc các chỉ số Web Vitals bằng CDP Performance domain APIs.
- **Task 1.12**: [Coder] - Thiết lập cấu hình ngưỡng tối đa cho LCP, CLS từ tệp cấu hình dự án.
- **Task 1.13**: [Verifier] - Chỉ điểm các đối tượng DOM gây ra sự dịch chuyển giao diện lớn (CLS source).
- **Task 1.14**: [Architect] - Khai báo cấu trúc đối tượng `PerformanceFinding`.
- **Task 2.1**: [Architect] - Kết nối luồng đánh giá responsive với Design Knowledge Base của Design Authority.
- **Task 2.2**: [Coder] - Đo đạc tốc độ khung hình (frame rate) của trình duyệt khi chạy hoạt ảnh CSS.
- **Task 2.3**: [Verifier] - Tích hợp điểm số hiệu năng kém vào trọng số bỏ phiếu của Consensus Engine.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.4 -> Task 2.1
- **Parallel Tasks**: [Task 1.3, Task 1.5, Task 1.6], [Task 1.7, Task 1.8, Task 1.9, Task 1.10], [Task 1.11, Task 1.12, Task 1.13, Task 1.14], [Task 2.2, Task 2.3]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.4), Task 1.7 (blocks Task 1.8), Task 1.11 (blocks Task 1.13)
- **Independent Tasks**: Task 1.5, Task 2.2
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.5, Task 1.6 (Accessibility Engine auditing)
  - **Group 2**: Task 1.7, Task 1.8, Task 1.9, Task 1.10 (Responsive Engine breakpoints testing)
  - **Group 3**: Task 1.11, Task 1.12, Task 1.13, Task 1.14 (Performance Observer metrics capturing)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3 (Consensus and layout animation integrations)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/observers/accessibility/engine.py` | Create | Trình kiểm tra tuân thủ WCAG a11y |
| Task 1.4 | `vir_runtime/observers/accessibility/veto.py` | Create | Quản lý logic VETO của Accessibility |
| Task 1.7 | `vir_runtime/observers/responsive/engine.py` | Create | Trình kiểm tra breakpoint và tràn giao diện |
| Task 1.11| `vir_runtime/observers/performance/engine.py` | Create | Trình đo Web Vitals và CLS sources |
| Task 2.2 | `vir_runtime/observers/performance/fps.py` | Create | Bộ đo tốc độ khung hình và jank animation |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả API cho các lớp `AccessibilityObserver`, `ResponsiveObserver`, và `PerformanceObserver`.
- **Provider Pattern details**: Mẫu bọc các thư viện ngoài (như axe-core hay Playwright resize commands) che giấu cài đặt chi tiết của nhà cung cấp.
- **Data Flow / Sequence Flow**: Luồng thực thi khi đổi viewport -> chụp ảnh -> đo bounding boxes -> quét a11y -> đọc CDP performance -> đóng gói 3 đối tượng findings -> gửi Event Bus.
- **Migration Strategy & Testing Architecture**: Sử dụng các trang HTML tĩnh chứa các lỗi a11y, responsive và performance dựng sẵn để chạy kiểm thử tích hợp nội bộ.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_a11y_axe.py` (Mapped to Task 1.1): Xác thực phát hiện đúng nút bấm thiếu text nhãn alt.
  - `tests/unit/test_responsive_overflow.py` (Mapped to Task 1.9): Inject phần tử div rộng 500px trên viewport 320px; kiểm tra phát hiện thanh cuộn ngang thành công.
  - `tests/unit/test_performance_vitals.py` (Mapped to Task 1.11): Đảm bảo trích xuất chính xác LCP và TTFB từ CDP Performance domain.
- **Integration Tests**:
  - `tests/integration/test_a11y_veto_gate.py` (Mapped to Task 1.4): Chèn bẫy bàn phím (keyboard trap); đảm bảo engine phát lệnh VETO thành công chặn phát hành.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Phát hiện chính xác 100% bẫy bàn phím và lỗi tương phản WCAG nghiêm trọng để kích hoạt VETO.
  - [ ] Chụp ảnh và kiểm tra bố cục hoàn tất trên 6 breakpoint chỉ định trong < 5 giây.
  - [ ] Core Web Vitals ghi nhận đầy đủ 4 chỉ số cơ bản.
- **Phase 2 Exit Criteria**:
  - [ ] Bộ ghi FPS ghi nhận và cảnh báo đúng janky animation < 60fps.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Resize trình duyệt liên tục ở tần suất cao gây đơ đơ hoặc treo Playwright.
  - *Steps*: Giảm số lượng breakpoint xuống 3 breakpoint chính (mobile, tablet, desktop) và thêm thời gian trễ ổn định (stabilization delay).
  - *Recovery*: Đảm bảo tiến trình kiểm thử responsive chạy mượt mà không treo máy chủ kiểm thử.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Task 1.4 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.7 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.11| Yes | Yes | Yes | Yes | No | Yes | Yes |
| Task 2.2 | Yes | No | Yes | No | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-067_vir_observers_blueprint.md
- **Phase 2 Artifacts**: .agents/visual-runtime/config/vir_observers.yaml
- **Phase 3 Artifacts**: docs/adr/ADR-015_performance_observations.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch observers tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm đo lường responsive và performance có thể chạy song song vì độc lập về tài nguyên quan sát.
- **Expected token savings**: Tiết kiệm ~40% tokens nhờ viết test unit trên trang web giả lập tĩnh được nạp thẳng bằng Playwright đĩa cứng thay vì chạy trên ứng dụng thực tế.
- **Recommended execution strategy**: Hoàn thành sớm phần a11y quét lỗi axe-core trước khi mở rộng ra đo đạc hiệu năng hoạt ảnh phức tạp.

---

## Recommended Next Skill
/blueprint
