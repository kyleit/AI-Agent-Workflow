<!-- File path: docs/issues/FIX-022_fix_token_diff_select_flickering.md -->
---
artifact_type: fix-spec
issue_id: FIX-022
workflow: quick-fix
status: completed
---
# Fix Specification – Fix Token Diff Select Flickering

## 1. Issue Description
Khi người dùng bấm vào bộ chọn (select dropdown) trong phần "COMPARE REQUESTS (TOKEN DIFF)" (gồm `diff-select-a` và `diff-select-b`) trên giao diện Visualizer dashboard, bộ chọn bị chớp tắt liên tục (flicker) và tự động đóng lại, khiến người dùng không thể chọn được request để so sánh. Nguyên nhân do hàm cập nhật giao diện định kỳ tải lại dữ liệu và ghi đè nội dung `innerHTML` của các thẻ `<select>` một cách vô điều kiện, làm mất trạng thái mở của dropdown và mất focus.

## 2. Scope
- **In Scope**:
  - Cập nhật logic Javascript trong tệp `webview.html` để kiểm tra điều kiện trước khi cập nhật `innerHTML` của các bộ chọn `diff-select-a` và `diff-select-b`.
  - Chỉ ghi đè `innerHTML` khi nội dung HTML mới khác nội dung hiện tại và phần tử đó không đang được người dùng tương tác (không có focus: `document.activeElement !== select`).
  - Đảm bảo biên dịch lại `webview.html` sang `webviewHtml.ts` thông qua tệp `build.js` trong thư mục `extensions/visualizer`.
- **Out of Scope**:
  - Không thay đổi cấu trúc dữ liệu gửi từ backend hoặc thay đổi cách lưu trữ lịch sử request.
  - Không thiết kế lại giao diện của phần Compare Requests.
