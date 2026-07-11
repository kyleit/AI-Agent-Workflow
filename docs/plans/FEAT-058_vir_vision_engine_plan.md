<!-- File path: docs/plans/FEAT-058_vir_vision_engine_plan.md -->

---
feature_id: FEAT-058
feature_name: Visual Intelligence Runtime — Vision Engine (5-Layer Architecture)
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-058_vir_vision_engine.md
next_artifact: ../designs/FEAT-058_vir_vision_engine_blueprint.md
---

# FEAT-058: Visual Intelligence Runtime — Vision Engine (5-Layer Architecture)

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Establish DOM bounding boxes and computed styles inspector (Layer 1) | [x] |
| FR-02 | Phase 1 | Task 1.2 | Create screenshot comparison and pixel diff analysis runner (Layer 2) | [x] |
| FR-06 | Phase 1 | Task 1.3 | Implement layer priority execution logic dispatcher | [x] |
| FR-07 | Phase 1 | Task 1.4 | Publish visual findings as Evidence objects to Event Bus | [x] |
| FR-08 | Phase 1 | Task 1.5 | Calculate confidence scoring dynamically for Layer 1 & 2 findings | [x] |
| FR-10 | Phase 1 | Task 1.6 | Capture page screenshots across multiple viewport breakpoints | [x] |
| FR-11 | Phase 1 | Task 1.7 | Apply pixel comparison tolerance thresholds and ignore regions | [x] |
| FR-12 | Phase 1 | Task 1.8 | Output annotated screenshots with highlighted bounding box overlays | [x] |
| FR-03 | Phase 2 | Task 2.1 | Integrate canvas and PDF OCR character extraction (Layer 3) | [x] |
| FR-04 | Phase 2 | Task 2.2 | Establish VLM semantic review prompt runner (Layer 4) | [x] |
| FR-09 | Phase 2 | Task 2.3 | Enforce VLM corroboration checks before finalizing verdicts | [x] |
| FR-13 | Phase 2 | Task 2.4 | Implement accessibility visual checks (contrast, focus visibility) | [x] |
| FR-05 | Phase 3 | Task 3.1 | Integrate YOLO canvas object detection classifier (Layer 5) | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai bộ phân tích DOM và Computed Style.
- **Task 1.2**: [Coder] - Tích hợp so sánh pixel ảnh với baseline qua Pixelmatch.
- **Task 1.3**: [Architect] - Thiết lập luồng ngắt sớm nếu lớp quan sát hiện tại đạt độ tin cậy.
- **Task 1.4**: [Coder] - Đóng gói và phát hành visual findings thành Evidence.
- **Task 1.5**: [Architect] - Định mức độ tin cậy riêng cho Layer 1 (phân tích DOM) và Layer 2 (Pixel).
- **Task 1.6**: [Coder] - Xử lý chụp ảnh hàng loạt ở các breakpoint màn hình.
- **Task 1.7**: [Verifier] - Triển khai bộ lọc tọa độ và CSS selector cần bỏ qua so sánh pixel.
- **Task 1.8**: [Coder] - Viết module vẽ khung đỏ (red box border overlay) đánh dấu lỗi lên screenshot.
- **Task 2.1**: [Coder] - Nạp thư viện OCR để lấy văn bản trên thẻ canvas.
- **Task 2.2**: [Coder] - Triển khai gửi ảnh sang VLM (Ollama/Gemini) phân tích.
- **Task 2.3**: [Verifier] - Cài đặt kiểm tra chéo, đánh dấu cờ `requires_corroboration` cho VLM findings.
- **Task 2.4**: [Verifier] - Tính toán độ tương phản (contrast ratio) theo công thức WCAG 2.1.
- **Task 3.1**: [Coder] - Tích hợp mô hình YOLO nhận dạng các widget đặc biệt trên Canvas.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.8 -> Task 2.4
- **Parallel Tasks**: [Task 1.5, Task 1.6, Task 1.7], [Task 2.1, Task 2.2], [Task 3.1]
- **Blocking Tasks**: Task 1.2 (blocks Task 1.8), Task 2.2 (blocks Task 2.3)
- **Independent Tasks**: Task 1.3, Task 1.4
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.8, Task 1.7 (Visual inspection core pipeline)
  - **Group 2**: Task 1.3, Task 1.4, Task 1.5, Task 1.6 (Orchestration mapping & metadata)
  - **Group 3**: Task 2.1, Task 2.2, Task 2.3, Task 2.4 (Advanced OCR/VLM and A11y observers)
  - **Group 4**: Task 3.1 (CV canvas models integration)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `vir_runtime/sensory/vision/dom_inspector.py` | Create | Phân tích DOM cấu trúc và computed styles |
| Task 1.2 | `vir_runtime/sensory/vision/pixel_comparer.py` | Create | So sánh pixel với baselines |
| Task 1.3 | `vir_runtime/sensory/vision/engine.py` | Create | Điều phối 5 lớp nhận diện Vision |
| Task 1.7 | `vir_runtime/sensory/vision/ignore_regions.py` | Create | Phân tích vùng tọa độ và selectors loại trừ |
| Task 1.8 | `vir_runtime/sensory/vision/annotator.py` | Create | Chụp và khoanh vùng tô đỏ lỗi lên ảnh |
| Task 2.1 | `vir_runtime/sensory/vision/ocr_reader.py` | Create | Nhận diện chữ dạng ảnh trên Canvas |
| Task 2.2 | `vir_runtime/sensory/vision/vlm_analyser.py` | Create | Trình phân tích ngữ nghĩa bằng mô hình lớn |
| Task 2.4 | `vir_runtime/sensory/vision/a11y_contrast.py` | Create | Kiểm tra tương phản màu sắc |
| Task 3.1 | `vir_runtime/sensory/vision/cv_yolo.py` | Create | Bộ phân tích mô hình YOLO ngoài |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Thiết kế lớp `VisionEngine` điều phối 5 adapter layer riêng lẻ.
- **Provider Pattern details**: Định dạng cấu trúc đầu vào và đầu ra của `VisionAdapter` che giấu công cụ so sánh.
- **Data Flow / Sequence Flow**: Vẽ luồng từ lúc nhận được yêu cầu chụp giao diện -> gọi Playwright lấy screenshot -> nạp baseline -> tính sai khác -> vẽ đè khung đỏ nếu có lỗi -> xuất Evidence.
- **Migration Strategy & Testing Architecture**: Chạy thử nghiệm sử dụng các fixture ảnh mẫu để kiểm tra độ nhạy của bộ pixel diff.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_dom_inspector.py` (Mapped to Task 1.1): Xác thực lấy đúng bounding box và z-index của các thẻ.
  - `tests/unit/test_pixel_match.py` (Mapped to Task 1.2): Đảm bảo phát hiện đúng sai lệch 5px và bỏ qua vùng ignore.
  - `tests/unit/test_contrast_calculator.py` (Mapped to Task 2.4): Thử nghiệm tính tương phản chữ đen nền trắng (21:1) và chữ xám nền xám (vi phạm).
- **Integration Tests**:
  - `tests/integration/test_vision_pipeline.py` (Mapped to Task 1.3): Đảm bảo nếu lớp DOM trả về độ tin cậy tuyệt đối, hệ thống sẽ ngắt và không gọi VLM.
  - `tests/integration/test_vlm_corroboration.py` (Mapped to Task 2.3): Đảm bảo phát hiện VLM đơn lẻ không có corroboration bị bỏ qua hoặc hạ điểm.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các bài so sánh ảnh với baseline chạy thành công trong < 2s.
  - [ ] Bộ vẽ annotation khoanh vùng lỗi xuất ra tệp ảnh dạng png hợp lệ.
  - [ ] Bỏ qua đúng các vùng ignore được cấu hình.
- **Phase 2 Exit Criteria**:
  - [ ] OCR đọc và trích xuất thành công chuỗi chữ dạng text từ thẻ Canvas.
  - [ ] Công thức tương phản màu sắc đạt độ chính xác tương đương tiêu chuẩn WCAG.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: So sánh pixel chiếm quá nhiều tài nguyên đĩa và gây chậm trễ nghiêm trọng cho CI/CD.
  - *Steps*: Tăng ngưỡng so sánh pixel hoặc tạm tắt Layer 2, khôi phục cấu hình vision ban đầu.
  - *Recovery*: Trả về chạy kiểm thử DOM thuần túy (Layer 1) để bảo toàn tiến độ phát hành.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | No | No | No |
| Task 1.2 | Yes | Yes | Yes | Yes | No | Yes | Yes |
| Task 1.8 | Yes | No | No | Yes | Yes | Yes | No |
| Task 2.2 | Yes | Yes | Yes | Yes | Yes | Yes | No |
| Task 2.4 | Yes | Yes | Yes | No | Yes | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-058_vir_vision_engine_blueprint.md
- **Phase 2 Artifacts**: vir_runtime/sensory/vision/vlm_analyser.py
- **Phase 3 Artifacts**: vir_runtime/sensory/vision/cv_yolo.py

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Phân tích logic so sánh ảnh tốn khoảng ~5,500 tokens.
- **Parallel execution opportunities**: Viết code nạp cấu hình và ignore regions (Task 1.5, 1.7) song song với lõi dom_inspector.py.
- **Expected token savings**: Tiết kiệm ~35% tokens nhờ chạy các test case visual cô lập trên fixture ảnh đĩa cứng mà không cần khởi tạo Browser.
- **Recommended execution strategy**: Phát triển hoàn thiện Layer 1 và Layer 2 trước khi thiết kế kết nối với VLM API.

---

## Recommended Next Skill
/blueprint
