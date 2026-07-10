---
feature_id: FEAT-030
feature_name: Fix Incorrect Context Warning Logic
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-030_fix_incorrect_context_warning_logic_plan.md
---

# Master Requirement Document – Fix Incorrect Context Warning Logic

## 1. Feature ID & Name
- **Feature ID**: FEAT-030
- **Feature Name**: Fix Incorrect Context Warning Logic

## 2. Original Idea
Fix incorrect context warning logic in AIWF. Currently, a 247.2K / 2.0M active context (12.4%) wrongly triggers a "Context high" warning. The warning logic must be percentage-based and scale automatically. Context Capacity must be separated from Cost Efficiency. Thresholds must be moved to runtime configuration.

## 3. Business Problem
- **Problem**: Giao diện hiển thị cảnh báo "Context high" dựa trên ngưỡng cứng (160K tokens) thay vì tỷ lệ phần trăm động so với giới hạn ngữ cảnh thực tế của mô hình (limit_tokens). Ngoài ra, các cảnh báo về chi phí và hiệu năng (Cost Efficiency) bị trộn lẫn với cảnh báo đầy context, gây khó hiểu cho người dùng.
- **Why it matters**: Làm giảm trải nghiệm người dùng, tạo cảnh báo giả khi dung lượng context thực tế vẫn còn rất rộng (87.6% trống), và che khuất các cảnh báo về chi phí thực tế.
- **Who is affected**: Lập trình viên và AI agents quan sát telemetry của hệ thống.
- **Expected outcome**: 
  - Cảnh báo Context dựa trên phần trăm động so với limit_tokens (Healthy, Warning, High, Critical).
  - Tách biệt cảnh báo Context Capacity và Cost/Efficiency thành các thông điệp khác nhau.
  - Ngưỡng cấu hình được lưu trong file cấu hình để dễ dàng thay đổi.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01 (Cấu hình động): Thêm cấu hình `"telemetry"` vào `workflow.config.json` để quy định các ngưỡng phần trăm và chi phí.
  - FR-02 (Đồng bộ cấu hình): Truyền cấu hình telemetry vào session và lưu trữ trong `runtime.json` dưới khóa `telemetry_config`.
  - FR-03 (Phân tách UX cảnh báo):
    - Context Capacity: Cảnh báo động (Healthy < 60%, Warning 60-80%, High 80-95%, Critical 95-100%).
    - Cost Efficiency: Hộp cảnh báo riêng cho chi phí USD cao, tỷ lệ I/O kém, redundant reads lớn, v.v.
  - FR-04 (Kiểm thử tự động): Viết các test case tự động kiểm thử các mức phần trăm khác nhau và trường hợp Context thấp nhưng Chi phí cao.
- **Non-functional Requirements**:
  - NFR-01 (Hiệu năng): Việc phân tích và hiển thị không gây trễ giao diện.
  - NFR-02 (Khả năng tương thích ngược): Nếu cấu hình bị thiếu, sử dụng giá trị mặc định hợp lý.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Mức mặc định của các ngưỡng là bao nhiêu? | Context: 60% (Warning), 80% (High), 95% (Critical). Chi phí: $10 USD (Warning), $50 USD (Critical). |
| Có hiển thị cả hai loại cảnh báo cùng lúc nếu cả hai đều vượt ngưỡng không? | Có, giao diện hiển thị các cảnh báo này trong các phần hoặc dòng thông điệp phân tách rõ ràng trong alert box. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Hệ thống sử dụng `.agents/workflow.config.json` làm tệp cấu hình dự án, và chia tách trạng thái session trong `.agents/state/`. Giao diện `webview.html` hiển thị cảnh báo dựa trên giá trị cứng `activeTotal > 160000`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Project Configuration | [.agents/workflow.config.json](file:///e:/AgentsProject/.agents/workflow.config.json) | Cần bổ sung khối cấu hình telemetry. |
| Session & State Sync | [.agents/skills/workflow-runtime/scripts/session.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/session.py) & [state_sync.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/state_sync.py) | Cần đọc và đồng bộ cấu hình telemetry vào tệp trạng thái. |
| Extension Webview | [extensions/visualizer/resources/webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html) | Cần cập nhật JavaScript để hiển thị cảnh báo theo cấu hình động và phân tách hai chỉ số. |

## 9. Solution Options Evaluated

### Option A: Phân tách toàn diện, Đồng bộ Cấu hình động & Thử nghiệm tự động (Khuyên dùng)
- **Overview**: Thêm cấu hình trong `workflow.config.json`, đồng bộ qua `runtime.json` -> Visualizer -> `webview.html`. Phân tách UX hiển thị và viết unit tests kiểm chứng.
- **Complexity**: Medium
- **Risk**: Low
- **Performance**: High

### Option B: Sửa cứng ngưỡng phần trăm ở Frontend (webview.html)
- **Overview**: Tính toán lại phần trăm trực tiếp trong `webview.html` dựa trên `activePercentage` thay vì ngưỡng 160K tokens. Không dùng file cấu hình.
- **Complexity**: Low
- **Risk**: Low

## 10. Solution Comparison Table
| Criteria | Option A (Khuyên dùng) | Option B |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Low |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | High |

## 11. Selected Solution
- **Choice**: Option A
- **Why Selected**: Đáp ứng đầy đủ các yêu cầu thiết kế của Ba về tính động, cấu hình hóa và phân tách rõ ràng hai loại cảnh báo ngữ cảnh và chi phí.

## 12. Risks & Assumptions
- **Risks**: Trực quan hóa tiến trình nếu không tìm thấy cấu hình. -> *Mitigation*: Sử dụng fallback mặc định thông minh trong `session.py` và `webview.html`.

## 13. Acceptance Criteria
- [ ] Giao diện hiển thị đúng trạng thái cảnh báo động của Context theo tỷ lệ phần trăm cấu hình.
- [ ] Hộp cảnh báo Cost hiển thị độc lập khi chi phí tích lũy hoặc độ hiệu quả vượt ngưỡng.
- [ ] Các unit test tự động xác thực chính xác các ngưỡng ngữ cảnh và chi phí.

---

## 14. Final Planning Prompt
Thực hiện Option A:
- Khai báo cấu hình telemetry trong `workflow.config.json`.
- Truyền cấu hình telemetry qua `session.py` và `state_sync.py` lưu vào `runtime.json`.
- Cập nhật Webview để đọc cấu hình và hiển thị cảnh báo phân tách.
- Viết unit test cho các mức phần trăm 12%, 45%, 61%, 79%, 81%, 95%, 99% và test phân tách.
