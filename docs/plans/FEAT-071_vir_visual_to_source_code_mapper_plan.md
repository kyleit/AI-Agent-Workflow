<!-- File path: docs/plans/FEAT-071_vir_visual_to_source_code_mapper_plan.md -->

---
feature_id: FEAT-071
feature_name: Visual Intelligence Runtime — Visual-to-Source Code Mapper
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-071_vir_visual_to_source_code_mapper.md
next_artifact: ../designs/FEAT-071_vir_visual_to_source_code_mapper_blueprint.md
---

# FEAT-071: Visual Intelligence Runtime — Visual-to-Source Code Mapper

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Extract internal framework descriptors from runtime DOM nodes | [x] |
| FR-02 | Phase 1 | Task 1.2 | Query React Fiber metadata (`__reactFiber$`) component details | [x] |
| FR-03 | Phase 1 | Task 1.3 | Query Vue virtual DOM metadata (`__vnode`) component details | [x] |
| FR-04 | Phase 1 | Task 1.4 | Query Svelte element markers to locate origin Svelte files | [x] |
| FR-06 | Phase 1 | Task 1.5 | Parse sourcemap files (`.map`) to translate minified TS files | [x] |
| FR-07 | Phase 1 | Task 1.6 | Trace CSS classes declarations back to source code layouts | [x] |
| FR-12 | Phase 1 | Task 1.7 | Implement fallback mechanisms using DOM text grepping | [x] |
| FR-13 | Phase 1 | Task 1.8 | Return ranked candidate source lists with confidence weights | [x] |
| FR-14 | Phase 1 | Task 1.9 | Enforce file edit boundaries checks based on Blueprint | [x] |
| FR-15 | Phase 1 | Task 1.10| Block mapping out-of-bounds to external node modules | [x] |
| FR-05 | Phase 2 | Task 2.1 | Query Angular debug context backing component classes | [x] |
| FR-08 | Phase 2 | Task 2.2 | Map event handlers listeners to TS/JS function blocks | [x] |
| FR-09 | Phase 2 | Task 2.3 | Trace reactive state data bindings (Redux/Pinia stores) | [x] |
| FR-10 | Phase 2 | Task 2.4 | Map virtual DOM templates to render functions code blocks | [x] |
| FR-11 | Phase 2 | Task 2.5 | Support Webpack/Vite bundlers source structures adapters | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Viết tập lệnh JS nhúng (injection script) để trích xuất thuộc tính metadata của thẻ DOM.
- **Task 1.2**: [Coder] - Trích xuất tệp và dòng code JSX từ thuộc tính React Fiber.
- **Task 1.3**: [Coder] - Trích xuất tệp SFC `.vue` từ đối tượng Vue VNode.
- **Task 1.4**: [Coder] - Trích xuất tệp `.svelte` dựa trên svelte internal attributes.
- **Task 1.5**: [Coder] - Tích hợp thư viện python `sourcemap` để dịch tọa độ JS bundle về TS.
- **Task 1.6**: [Coder] - Trích xuất dòng khai báo lớp CSS Modules hoặc lớp Tailwind CSS tương ứng.
- **Task 1.7**: [Verifier] - Triển khai bộ tìm kiếm văn bản thô (DOM text grepper) và class name nếu thiếu map.
- **Task 1.8**: [Architect] - Thuật toán đánh giá trọng số tin cậy (như khớp tên thẻ, khớp class) để xếp hạng ứng viên.
- **Task 1.9**: [Verifier] - Triển khai bộ chặn kiểm tra tệp tin muốn ghi đè so với danh mục tệp cho phép của Blueprint.
- **Task 1.10**: [Verifier] - Chặn phân tích và ánh xạ ngược vào thư mục `node_modules` hoặc thư viện ngoài.
- **Task 2.1**: [Coder] - Trích xuất Angular component class bằng cách chạy lệnh `ng.getComponent`.
- **Task 2.2**: [Coder] - Trích xuất tên hàm và dòng khai báo của listener (ví dụ `onClick`).
- **Task 2.3**: [Coder] - Lấy thông tin tệp tin khai báo store quản lý state tương ứng của element.
- **Task 2.4**: [Architect] - Xây dựng ánh xạ từ cấu trúc vdom về các render function hoặc template HTML vật lý.
- **Task 2.5**: [Coder] - Tinh chỉnh các tham số cấu hình thích ứng với Vite hoặc Webpack output.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> [Task 1.2, Task 1.3, Task 1.4] -> Task 1.5 -> Task 1.8 -> Task 1.9
- **Parallel Tasks**: [Task 1.2, Task 1.3, Task 1.4], [Task 1.6, Task 1.7, Task 1.10], [Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.2), Task 1.5 (blocks Task 1.8)
- **Independent Tasks**: Task 1.10, Task 2.5
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4 (Framework metadata scrapers core)
  - **Group 2**: Task 1.5, Task 1.6, Task 1.8 (Sourcemap and CSS trace mappers)
  - **Group 3**: Task 1.7, Task 1.9, Task 1.10 (Fallback searches & scope safety boundaries)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.3, Task 2.4, Task 2.5 (Advanced handlers & bundlers mapping)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/mapper/scraper.py` | Create | Nhúng JS và cào metadata của các framework |
| Task 1.5 | `vir_runtime/mapper/sourcemaps.py` | Create | Dịch tọa độ bundle JS sang TS |
| Task 1.6 | `vir_runtime/mapper/css.py` | Create | Ánh xạ CSS Modules và Tailwind styles |
| Task 1.7 | `vir_runtime/mapper/fallback.py` | Create | Tìm kiếm thô (grep) khi mất map |
| Task 1.8 | `vir_runtime/mapper/ranker.py` | Create | Xếp hạng và tính độ tin cậy ứng viên |
| Task 1.9 | `vir_runtime/mapper/scope_gate.py` | Create | Kiểm duyệt an toàn phạm vi Blueprint |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Cấu trúc các lớp `SourceLinker`, `MetadataScraper`, và `SourcemapResolver`.
- **Provider Pattern details**: Định dạng cấu trúc đầu ra `SourceCoordinate` (file path, line, column, confidence).
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận DOM node -> Scraper lấy fiber meta -> nạp sourcemap -> dịch về JSX source file -> kiểm tra scope -> xếp hạng candidate -> xuất kết quả.
- **Migration Strategy & Testing Architecture**: Dùng kịch bản test trang React build sẵn sourcemap tĩnh để kiểm chứng độ chính xác dịch dòng code.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_react_fiber.py` (Mapped to Task 1.2): Quét element React; xác nhận trả về đúng tệp JSX nguồn.
  - `tests/unit/test_sourcemap_resolver.py` (Mapped to Task 1.5): Dịch file bundle.js:12:43; kiểm tra khớp dòng TS nguồn.
  - `tests/unit/test_fallback_grep.py` (Mapped to Task 1.7): Kiểm thử tìm kiếm text độc bản; đảm bảo trả về đúng component candidate.
- **Integration Tests**:
  - `tests/integration/test_scope_enforcement.py` (Mapped to Task 1.9): Thử sửa đổi file nằm ngoài danh sách cho phép; xác định hệ thống phát lệnh cảnh báo.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] Ánh xạ thành công React Fiber và Vue VNode về đúng file và dòng code trong < 150ms.
  - [ ] Sourcemap phân tích và giải dịch tọa độ chính xác.
  - [ ] Chặn thành công các yêu cầu chỉnh sửa ngoài scope Blueprint.
- **Phase 2 Exit Criteria**:
  - [ ] Ánh xạ thành công click event listener về dòng khai báo hàm TS nguồn.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Thuộc tính React Fiber bị đổi tên hoặc không tồn tại trong bản build làm chương trình cào dữ liệu gặp lỗi crash liên tục.
  - *Steps*: Kích hoạt chế độ Fallback Grep search mặc định, tạm bỏ qua phân tích React Fiber, revert code `scraper.py`.
  - *Recovery Bluesteps*: Đảm bảo hệ thống tiếp tục chạy bằng tìm kiếm thô.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | Yes | No | Yes | No |
| Task 1.5 | Yes | Yes | Yes | No | No | No | No |
| Task 1.8 | Yes | Yes | Yes | Yes | Yes | Yes | No |
| Task 1.9 | Yes | Yes | Yes | No | Yes | No | No |
| Task 2.2 | Yes | No | Yes | Yes | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-071_vir_visual_to_source_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/mapper/ranker.py
- **Phase 3 Artifacts**: docs/adr/ADR-019_sourcemap_resolutions.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch source mapper tiêu tốn ~5,500 tokens.
- **Parallel execution opportunities**: Nhóm cào metadata framework (Task 1.2, 1.3, 1.4) chạy song song với css.py.
- **Expected token savings**: Tiết kiệm ~45% tokens nhờ chạy các kiểm thử dịch sourcemap trên tệp map giả lập không cần khởi động tiến trình Playwright hay mở trang web thực tế.
- **Recommended execution strategy**: Hoàn thành sớm phần dịch sourcemap (sourcemaps.py) trước khi viết logic xếp hạng ứng viên phức tạp.

---

## Recommended Next Skill
/blueprint
