<!-- File path: docs/quick/QUICK-003_skills_update_notification_improvements.md -->

---
artifact_type: quick-feature
feature_id: QUICK-003
workflow: quick-feature
architecture_impact: low
adr_required: false
status: approved
---

# Mini Feature Specification – Skills Update Notification Improvements

## 1. Feature Goal
Cải tiến trải nghiệm người dùng (UX) và bảo mật của tính năng thông báo cập nhật Kỹ năng AI (Skills Auto-Update Notification) trên visualizer extension:
1. Loại bỏ nút cập nhật tự động bằng Terminal để nhà phát triển chủ động pull mã nguồn an toàn từ GitHub.
2. Phân tách rõ ràng giữa hai nút: Nút đóng tạm thời (Dismiss / X) và nút bỏ qua phiên bản này vĩnh viễn (Skip Version).
3. Thiết kế và tích hợp một hộp thoại xác nhận Custom HTML Confirm phong cách glassmorphic (không dùng confirm mặc định của trình duyệt) để xác nhận khi người dùng nhấn bỏ qua vĩnh viễn.

## 2. Business Value
- Nâng cao tính an toàn bảo mật, tránh tự ý thực thi các lệnh terminal ngoài tầm kiểm soát.
- Cải thiện trải nghiệm người dùng, tránh gây phiền nhiễu khi lập trình viên chưa muốn cập nhật.

## 3. Existing Context
- Tệp giao diện: `extensions/visualizer/resources/webview.html`
- Tệp logic extension: `extensions/visualizer/src/extension.ts`
- Tệp snapshot giao diện: `extensions/visualizer/src/webviewHtml.ts`

## 4. Scope
- **In Scope**:
  - Loại bỏ hoàn toàn sự kiện `TRIGGER_UPDATE` và phương thức `triggerSkillsUpdate()`.
  - Bổ sung CSS, HTML và JS click listener cho nút đóng banner X (tắt tạm thời) và nút Skip Version (bỏ qua vĩnh viễn).
  - Tích hợp hộp thoại Custom HTML Confirm (Custom Modal) phong cách glassmorphic để xác nhận hành động bỏ qua.
  - Tích hợp gửi tin nhắn `SKIP_VERSION` về Extension khi người dùng xác nhận trên Modal để lưu phiên bản bị bỏ qua vào `vscode.ExtensionContext.globalState`.
  - Tích hợp lưu phiên bản bị bỏ qua vào `localStorage` của trình duyệt khi test offline.
  - Lọc bỏ thông báo nếu phiên bản mới trên GitHub trùng khớp với phiên bản đã bị bỏ qua.
- **Out of Scope**:
  - Tự động chạy script terminal nâng cấp ngầm.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | `extensions/visualizer/resources/webview.html` | Cập nhật banner HTML/CSS, chèn Custom Modal, thêm listener các nút |
| Modify | `extensions/visualizer/src/extension.ts` | Nhận message `SKIP_VERSION` lưu vào globalState và lọc tin nhắn cập nhật |
| Modify | `extensions/visualizer/src/webviewHtml.ts` | Biên dịch đồng bộ từ `webview.html` |

## 6. Proposed Changes
- **Trong `extension.ts`**:
  - Nhận `ExtensionContext` tại constructor của `AIWorkflowViewProvider`.
  - Lắng nghe sự kiện `SKIP_VERSION` và ghi vào `this._context.globalState.update('skippedSkillsVersion', version)`.
  - Trước khi gửi tin nhắn `UPDATE_AVAILABLE`, kiểm tra `remoteVersion !== skippedVersion`.
- **Trong `webview.html`**:
  - Chèn nút đóng X và nút Skip Version vào Banner HTML.
  - Thiết lập Custom Modal HTML và CSS để hiển thị hộp thoại xác nhận.
  - Khi click nút X, ẩn banner tạm thời trong phiên hiện tại (không lưu skip).
  - Khi click nút Skip Version, hiện Modal Confirm. Nếu nhấn xác nhận trên Modal, ẩn banner và gửi SKIP_VERSION về extension/trình duyệt.

## 7. Risks
- **Risk**: Phiên bản bị bỏ qua bị kẹt mãi mãi → **Mitigation**: Chỉ so khớp bằng (equal) với phiên bản hiện tại trên GitHub. Khi GitHub có phiên bản mới hơn, hệ thống sẽ tự động hiển thị lại.

## 8. Acceptance Criteria
- [x] Không còn nút bấm `[Update Now]`, không tự ý mở terminal.
- [x] Phân tách nút đóng tạm thời (X) và bỏ qua vĩnh viễn (Skip Version).
- [x] Bấm Skip Version hiển thị Custom HTML Confirm phong cách glassmorphic.
- [x] Bấm nút tắt tạm thời (X) chỉ ẩn banner trong phiên hiện tại, F5 hiển thị lại.
- [x] Xác nhận trên Custom Confirm Modal sẽ ẩn banner vĩnh viễn cho phiên bản đó.
- [x] Tối ưu hóa CSS banner (white-space: nowrap cho nút bấm) và lồng icon lấp lánh bên trong khối text để hiển thị thẳng hàng hoàn hảo trên màn hình sidebar hẹp của VS Code.


## 9. Test Plan
- **Verification**: Run `npm run compile` trong thư mục extension.
- **Manual Check**: Mở trực tiếp `webview.html` trên trình duyệt Chrome, kiểm tra hiển thị Modal và các nút bấm, tắt và reload lại trang để xác nhận các trạng thái tắt/bỏ qua vĩnh viễn hoạt động chính xác.

