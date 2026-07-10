<!-- File path: docs/plans/FEAT-044_visualizer_tabbed_sidebar_plan.md -->

---
feature_id: FEAT-044
feature_name: Visualizer Tabbed Sidebar
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-044_visualizer_tabbed_sidebar.md
next_artifact: ../designs/FEAT-044_visualizer_tabbed_sidebar_blueprint.md
---

# FEAT-044: Visualizer Tabbed Sidebar

## Objective
- **Business Objective**: Tách biệt giao diện của thanh sidebar tiện ích Visualizer thành 2 tab chính nhằm giảm thiểu sự chật chội và rối mắt khi hiển thị quá nhiều thông tin trên giao diện dọc hẹp của VS Code.
- **Expected Outcome**: Người dùng có thể chuyển đổi nhanh giữa hai tab Checkpoints (quản lý tiến trình) và Context / Statistics (quản lý dữ liệu token/cost) một cách mượt mà và trực quan, trong khi thông tin phiên làm việc (Workflow Session) và bản quyền (Framework Author) vẫn luôn cố định. Các hộp chọn so sánh (select boxes) được thiết kế tùy biến (custom select UI) để tối ưu tính thẩm mỹ và chuyên nghiệp.

## Scope

### Included
- Nhóm và phân tách các thành phần hiển thị hiện tại vào 2 khu vực panel khác nhau trong mã giao diện.
- Thiết kế hệ thống tab gồm 2 nút chuyển đổi trực quan, hiển thị rõ ràng tab nào đang được kích hoạt.
- Đảm bảo giữ nguyên hộp thông tin Workflow Session ở đầu và Framework Author ở cuối giao diện ở mọi tab.
- Lưu giữ trạng thái tab đang hoạt động để tránh bị reset về mặc định khi làm mới dữ liệu từ backend.
- Chuyển đổi toàn bộ các hộp chọn so sánh (select boxes) từ mặc định của trình duyệt sang Custom Select UI cao cấp, đẹp mắt.
- Tích hợp tiêu chuẩn truy cập (Accessibility - ARIA roles) cho các tab.

### Excluded
- Không thiết kế lại thuật toán đo lường token/cost hay cấu trúc dữ liệu gửi từ backend.
- Không thay đổi hành động ghi dữ liệu hay lịch sử request.

## Project Impact
- **Visualizer Extension Frontend**: Tệp giao diện `webview.html` và tệp biên dịch tự động `webviewHtml.ts`.
- **Extension Build Pipeline**: Chạy tập lệnh `node build.js` để đồng bộ hóa mã nguồn giao diện sau chỉnh sửa.

## Dependencies
- Tiện ích Visualizer hoạt động và render bình thường bằng tệp `webviewHtml.ts` hiện tại.
- Trình biên dịch TypeScript hoạt động ổn định để biên dịch mã nguồn của extension.

## Risks
- **Trạng thái Tab bị mất khi làm mới giao diện**: Khi dữ liệu session được cập nhật liên tục từ backend, nếu không quản lý tốt, tab có thể tự động nhảy về tab mặc định.
  - *Giảm thiểu*: Lưu trạng thái tab hiện tại vào một biến JavaScript trong Webview và kiểm tra/áp dụng lại display mode sau mỗi đợt gọi hàm render `updateUI`.
- **Lỗi chớp tắt hoặc mất tương tác trên Custom Select**: Do custom select tự viết bằng HTML/CSS/JS, nếu không tối ưu, có thể xảy ra hiện tượng mất sự kiện click/change hoặc mất dữ liệu khi UI re-render.
  - *Giảm thiểu*: Thiết kế logic binding của custom select tách biệt khỏi luồng re-render định kỳ hoặc áp dụng so sánh dữ liệu trước khi vẽ lại.

## Acceptance Criteria
- [ ] Hộp thông tin Workflow Session và Framework Author luôn hiển thị cố định ở mọi tab.
- [ ] Tab Checkpoints chỉ hiển thị checkpoint timeline và chi tiết log.
- [ ] Tab Context / Statistics hiển thị đầy đủ các thông số token, cost, biểu đồ và so sánh token.
- [ ] Nhấp đổi tab hoạt động mượt mà, chuyển đổi tức thì, màu sắc/kiểu dáng nút tab thay đổi rõ ràng theo trạng thái active.
- [ ] Khi làm mới dữ liệu từ backend, tab đang active không bị thay đổi.
- [ ] Tất cả select box so sánh được thay thế bằng Custom Select UI có thiết kế hiện đại, mượt mà và tương tác bình thường không bị lỗi chớp tắt.
- [ ] Biên dịch TypeScript và đóng gói extension thành công không có lỗi.

## Deliverables
- Tệp giao diện đã sửa đổi: `extensions/visualizer/resources/webview.html`.
- Tệp biên dịch tự động: `extensions/visualizer/src/webviewHtml.ts`.

## Estimated Complexity
- **Medium**: Tái cấu trúc cấu trúc HTML hiện có, quản lý trạng thái tab khi re-render định kỳ, và viết Custom Select UI đẹp mắt, xử lý tương tác an toàn.

## Recommended Blueprint Focus
- Tập trung vào cấu trúc CSS của hệ thống Tab và Custom Select UI, đảm bảo tuân thủ màu sắc theme của VS Code.
- Thiết kế chi tiết logic JS xử lý ẩn/hiện panel tab, lưu giữ biến `currentActiveTab`.
- Thiết kế Custom Select UI bằng HTML/CSS/JS (gồm dropdown container, selected text, options list), xử lý đóng mở khi click ra ngoài, và gán dữ liệu lựa chọn chuẩn xác.

## Recommended Next Skill
/blueprint
