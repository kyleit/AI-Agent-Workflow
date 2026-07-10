---
feature_id: FEAT-031
feature_name: Redesign AIWF Context Status UX
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../designs/FEAT-030_fix_incorrect_context_warning_logic_blueprint.md
next_artifact: ../plans/FEAT-031_redesign_aiwf_context_status_ux_plan.md
---

# Master Requirement Document – Redesign AIWF Context Status UX

## 1. Feature ID & Name
- **Feature ID**: FEAT-031
- **Feature Name**: Redesign AIWF Context Status UX

## 2. Original Idea
Redesign AIWF Context Status UX. Currently, healthy states display alert boxes with warning icons, and context capacity metrics are mixed with efficiency metrics. We need 4 explicit status levels (Healthy, Warning, High, Critical) with distinct UI presentations, and complete separation of Context Analytics, API Usage, and Efficiency Analysis into distinct cards. Themes must be configurable.

## 3. Business Problem
- **Problem**: Giao diện hiển thị cảnh báo Context hiện tại sử dụng chung một hộp thông tin cảnh báo màu vàng với icon cảnh báo (⚠️) ngay cả khi trạng thái hoàn toàn bình thường/lành mạnh (Healthy). Điều này gây hiểu lầm cho người dùng (False Positive UX). Ngoài ra, các chỉ số dung lượng context và hiệu suất/chi phí API bị gộp chung làm nhiễu thông tin.
- **Why it matters**: Trải nghiệm UX thiếu chuyên nghiệp, không làm nổi bật được mức độ nghiêm trọng khi thực sự xảy ra quá tải ngữ cảnh (Context Overflow) hoặc lãng phí chi phí.
- **Who is affected**: Lập trình viên và AI agents vận hành hệ thống.
- **Expected outcome**:
  - Phân tách giao diện thành 3 card riêng biệt: **Context Analytics** (Dung lượng ngữ cảnh), **API Usage** (Chi phí và số lượng token tích lũy), và **Efficiency Analysis** (Đánh giá hiệu suất và gợi ý tối ưu).
  - Trạng thái **Healthy** của Context sẽ sử dụng màu xanh lục (Green) kèm biểu tượng thành công (🟢) và hiển thị dạng thẻ thông tin trung tính/badge gọn gàng, không dùng hộp cảnh báo.
  - Các trạng thái Warning/High/Critical của Context và cảnh báo chi phí sẽ được hiển thị độc lập tại các card tương ứng với màu sắc và biểu tượng đặc trưng.
  - Hỗ trợ cấu hình theme (màu sắc, icon, ngưỡng) từ tệp cấu hình.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01 (Cấu hình Theme & Ngưỡng): Cập nhật `workflow.config.json` để cho phép cấu hình màu sắc, icon, và ngưỡng cho từng trạng thái:
    - `context_thresholds`: warning, high, critical.
    - `context_styles`: healthy, warning, high, critical (chứa màu sắc, mã màu viền, icon).
    - `cost_thresholds`: warning_usd, critical_usd.
  - FR-02 (Phân tách Giao diện):
    - Thay thế khối `workflow-usage-card` cũ bằng 3 card độc lập:
      - `Context Analytics`: Trạng thái Context, tokens hiện tại/tối đa, phần trăm sử dụng, số token còn lại, sparkline.
      - `API Usage`: Tổng Input, Output, Cache, Thinking tokens, số requests, tổng chi phí USD.
      - `Efficiency Analysis`: Tỷ lệ I/O, Cache Hit, Memory Hit, RAG Hit, số lượt đọc trùng lặp, ước tính tiết kiệm và cảnh báo chi phí.
  - FR-03 (Trực quan hóa Trạng thái Context):
    - Trạng thái Healthy: Dùng icon 🟢 (hoặc checkmark), không hiển thị hộp cảnh báo cảnh báo.
    - Trạng thái cảnh báo (Warning/High/Critical): Sử dụng hộp cảnh báo tương ứng với cấu hình màu sắc và icon (🟡/🟠/🔴).
- **Non-functional Requirements**:
  - NFR-01 (Hiệu ứng Micro-animations): Sử dụng các hiệu ứng chuyển đổi mượt mà khi trạng thái thay đổi.
  - NFR-02 (Khả năng tương thích ngược): Tự động nạp bộ theme/ngưỡng mặc định nếu cấu hình bị thiếu.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có hỗ trợ tùy biến các biểu tượng trạng thái bằng SVG hay Emoji không? | Cho phép cấu hình chuỗi ký tự emoji/icon (ví dụ: "🟢", "🟡", "🟠", "🔴") hoặc tên class biểu tượng. Mặc định dùng emoji dạng văn bản cho gọn gàng. |
| Nếu cả 2 cảnh báo về Context và Cost xảy ra cùng lúc thì sao? | Chúng sẽ hiển thị độc lập trong card tương ứng của mình (Cảnh báo Context trong card Context Analytics, Cảnh báo Cost trong card Efficiency Analysis). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Trạng thái telemetry được nạp từ `workflow_runtime.py` -> `runtime.json` -> Visualizer -> `webview.html`. Hiện tại, logic gom chung toàn bộ cảnh báo vào một hộp `optimizer-alert-box`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Project Configuration | [.agents/workflow.config.json](file:///e:/AgentsProject/.agents/workflow.config.json) | Thêm cấu hình style/theme động. |
| State Management | [state_sync.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/state_sync.py) | Đồng bộ cấu hình style động. |
| Visualizer Frontend | [webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html) | Thiết kế lại giao diện thành 3 card và áp dụng style động. |

## 9. Solution Options Evaluated

### Option A: Phân tách toàn diện, Thiết kế cấu hình Theme động & Đồng bộ trạng thái (Khuyên dùng)
- **Overview**: Cập nhật `workflow.config.json` với các cấu hình style/theme, đồng bộ qua session, thiết kế lại cấu trúc DOM của webview thành 3 card riêng biệt và áp dụng động CSS/HTML dựa trên cấu hình nhận được. Viết unit test cho logic hiển thị và phân tách.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Chỉ phân tách HTML/CSS cứng trong webview.html
- **Overview**: Sửa cứng giao diện 3 card và màu sắc trực tiếp trong Javascript của webview.html.
- **Complexity**: Low
- **Disadvantage**: Vi phạm yêu cầu cấu hình hóa theme động của Ba.

## 10. Selected Solution
- **Choice**: Option A
- **Why Selected**: Đảm bảo cấu hình hóa tối đa và phân tách UX sạch sẽ theo đúng tiêu chí thiết kế.

## 11. Risks & Assumptions
- **Risks**: Sự khác biệt về font chữ hiển thị emoji trên các hệ điều hành (Windows vs macOS). -> *Mitigation*: Sử dụng kết hợp CSS biến màu sắc (`var(--cyan)`, v.v.) và viền sáng neon để đảm bảo tính mỹ thuật trên mọi thiết bị.

## 12. Acceptance Criteria
- [ ] Giao diện có 3 card riêng biệt: Context Analytics, API Usage, Efficiency Analysis.
- [ ] Trạng thái Healthy của Context hiển thị màu xanh lục, không có hộp cảnh báo cảnh báo.
- [ ] Các cảnh báo chi phí hiển thị độc lập tại card Efficiency Analysis.
- [ ] Cấu hình style/theme được nạp từ tệp cấu hình động.
- [ ] Mọi unit test chạy thành công.
