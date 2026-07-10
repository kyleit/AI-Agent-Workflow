<!-- docs/brainstorming/FEAT-044_visualizer_tabbed_sidebar.md -->

---
feature_id: FEAT-044
feature_name: Visualizer Tabbed Sidebar
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-044_visualizer_tabbed_sidebar_plan.md
---

# Master Requirement Document – Visualizer Tabbed Sidebar

## 1. Feature ID & Name
- **Feature ID**: FEAT-044
- **Feature Name**: Visualizer Tabbed Sidebar

## 2. Original Idea
Redesign AI Workflow Visualizer Extension Tabs with Frontend Design Skill. The sidebar separates checkpoint progress from context/statistics panels using a clean tab system.

## 3. Business Problem
- **Problem**: Giao diện sidebar của Visualizer chứa quá nhiều phần thông tin (checkpoints, log, token usage, cost, request history, v.v.) hiển thị cùng lúc theo chiều dọc. Điều này làm cho giao diện trở nên cực kỳ chật chội, khó quét thông tin nhanh trên màn hình sidebar hẹp của VS Code.
- **Why it matters**: Lập trình viên khó theo dõi tiến trình của checkpoints và khó phân tích thông số token/cost một cách tập trung.
- **Who is affected**: Lập trình viên sử dụng Antigravity IDE/Visualizer Extension.
- **Expected outcome**: Giao diện được sắp xếp gọn gàng theo tab, chuyển đổi tức thì, giữ nguyên dữ liệu và trạng thái tương tác của người dùng.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Thêm hệ thống Tab gồm 2 Tab chính: **Checkpoints** và **Context / Statistics**.
  - FR-02: Hộp thông tin **Workflow Session** luôn hiển thị cố định ở trên đầu (phía trên hệ thống Tab) ở mọi chế độ Tab.
  - FR-03: Hộp thông tin **Framework Author** luôn hiển thị cố định ở dưới cùng (phía dưới nội dung Tab) ở mọi chế độ Tab.
  - FR-04: Tab **Checkpoints** chỉ hiển thị tiến trình checkpoints, timeline, checkpoints cards và log chi tiết.
  - FR-05: Tab **Context / Statistics** chứa toàn bộ các thẻ thông số khác: Context Usage, Token Usage, Cost, Runtime Insights, Context Breakdown, Token Diff Analysis, Request History.
  - FR-06: Nhấn vào Tab sẽ lập tức chuyển đổi hiển thị nội dung của Tab đó mà không làm chớp tắt hay mất dữ liệu đang tương tác. Trạng thái Tab hoạt động mặc định là `Checkpoints`.
  - FR-07: Khi dữ liệu tự động làm mới từ backend, trạng thái của Tab đang hoạt động phải được giữ nguyên.
  - FR-08: Các hộp chọn (select dropdowns) phải sử dụng bộ chọn tùy biến (custom select UI) thay vì thẻ select option thuần của trình duyệt để đảm bảo giao diện cao cấp (premium UI/UX) và đồng bộ với thiết kế chung.
- **Non-functional Requirements**:
  - NFR-01: Độ trễ chuyển Tab gần như bằng 0 (chuyển đổi bằng CSS display).
  - NFR-02: Accessibility: Sử dụng ARIA roles thích hợp (`role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected="true/false"`).
- **Technical Constraints**:
  - TC-01: Không được làm đứt gãy việc tải dữ liệu từ tệp trạng thái hoặc SQLite backend.
  - TC-02: Sửa đổi trực tiếp trong `extensions/visualizer/resources/webview.html` và biên dịch bằng `node build.js`.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Mặc định tab nào hiển thị đầu tiên? | Tab Checkpoints. |
| Có lưu trạng thái tab qua các phiên tải lại webview không? | Có, lưu giữ trong biến trạng thái trong khi webview đang hoạt động để tránh bị reset về mặc định khi nhận cập nhật dữ liệu. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `.agents/memory/project-summary.md`
- **Existing Architecture Summary**: visualizer là một VS Code extension sử dụng Webview để render giao diện, nguồn dữ liệu giao diện là tệp tin HTML tĩnh `webview.html` được biên dịch sang `webviewHtml.ts`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Webview Template | `extensions/visualizer/resources/webview.html` | Chứa giao diện chính và logic JavaScript cập nhật UI |
| Webview Codegen | `extensions/visualizer/build.js` | Tập lệnh biên dịch từ `webview.html` sang `webviewHtml.ts` |

## 9. Solution Options Evaluated

### Option A: Clean Native HTML/CSS + CSS Toggle display (display: none/block) (Selected)
- **Overview**: Sử dụng các thẻ `button` tiêu chuẩn của VS Code theme để làm nút bấm Tab. Bọc phần nội dung của Checkpoints và Context/Statistics vào hai div panel tương ứng và toggle ẩn hiện bằng cách gán `style.display = 'block'/'none'` bằng JavaScript.
- **Advantages**: Rất mượt mà, phản hồi tức thì, không làm mất event listeners của các thẻ bên trong (ví dụ select dropdowns).
- **Disadvantages**: Cả hai nội dung đều tồn tại trên DOM cùng lúc (nhưng không ảnh hưởng đến hiệu năng).

### Option B: Dynamic DOM Generation
- **Overview**: Tạo DOM động và vẽ lại HTML của tab hoạt động từ chuỗi template mỗi khi đổi tab.
- **Disadvantages**: Mất event listener của các select box so sánh và gây chớp tắt dữ liệu phức tạp.

## 10. Solution Comparison Table
| Criteria | Option A (Selected) | Option B |
|---|---|---|
| Complexity | Low | High |
| Risk | Low | Medium |
| Performance | Instant | Medium |
| Maintainability | Easy | Hard |
| Compatibility | Perfect | Low |

## 11. Selected Solution
- **Choice**: Option A — Clean Native HTML/CSS + CSS Toggle display
- **Why Selected**: Đảm bảo hiệu năng nhanh nhất, giữ nguyên trạng thái các select box so sánh token diff và tính đơn giản trong mã nguồn.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Lệch trạng thái tab khi reload toàn bộ Webview -> Giải pháp: Thiết lập tab mặc định ban đầu là Checkpoints.

## 13. Acceptance Criteria
- [ ] Tab Checkpoints chỉ hiển thị checkpoint timeline và logs.
- [ ] Tab Context / Statistics chỉ hiển thị các panel thống kê và so sánh token.
- [ ] Phần Workflow Session và Framework Author luôn hiển thị cố định ở đầu và cuối.
- [ ] Nhấp đổi tab hoạt động trơn tru, đổi kiểu dáng nút tab để thể hiện tab đang active rõ ràng.
- [ ] Làm mới dữ liệu không bị đổi/reset tab đang chọn.
- [ ] Các select box (hộp chọn so sánh) được thiết kế tùy biến (custom select UI) thay vì dùng select mặc định của trình duyệt để có giao diện cao cấp.

---

## 14. Final Planning Prompt

### Purpose
Tập hợp yêu cầu hoàn chỉnh cho bước Lập kế hoạch (Planning).

### Objectives & Selected Solution
Tạo hệ thống tab phân tách Checkpoint và Context/Statistics trên sidebar sử dụng Option A (display toggling). Tùy biến các select box so sánh thành custom select UI cao cấp.

### Functional Requirements
- Bọc checkpoint và logs vào Panel A.
- Bọc stats, usage và history vào Panel B.
- Giữ Workflow Session và Framework Author ở ngoài.
- Thêm hàng nút tab có ARIA roles.
- JavaScript click handler để ẩn/hiện panel và đổi active style của nút.
- updateUI giữ nguyên tab đang active.
- Chuyển đổi các thẻ select của trình duyệt sang Custom Select UI với thiết kế hiện đại, tinh tế.

### Verification Checklist
- [ ] `docs/plans/FEAT-044_visualizer_tabbed_sidebar_plan.md` được tạo và phê duyệt.
- [ ] Chuyển tab hoạt động bình thường, không reset khi cập nhật dữ liệu.
- [ ] Custom select hoạt động trơn tru, chọn được dữ liệu và không bị lỗi chớp tắt.
- [ ] Webview biên dịch thành công không có lỗi TypeScript.
