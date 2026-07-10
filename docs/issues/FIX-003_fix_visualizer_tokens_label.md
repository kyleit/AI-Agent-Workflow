<!-- File path: docs/issues/FIX-003_fix_visualizer_tokens_label.md -->

---
artifact_type: fix
issue_id: FIX-003
workflow: quick-fix
architecture_impact: low
adr_required: false
status: PASS
---

# Fix Document – Fix Visualizer Active Tokens Label Mismatch

## 1. Issue
Người dùng phản hồi rằng giao diện Visualizer hiển thị thông số không đồng nhất: Lượng token tiêu thụ hiển thị `8.3M / 2.0M tokens` nhưng thanh tiến độ và tỉ lệ phần trăm lại chỉ hiển thị `3.6%` (tương ứng khoảng `72K` tokens).

## 2. Symptoms
- Trên thanh tiến độ Workflow Usage, nhãn text hiển thị `[total_tokens] / [limit_tokens]` (ví dụ: `8.2M / 2.0M tokens`).
- Tỉ lệ phần trăm bên phải và thanh tiến độ hiển thị `[percentage]` (ví dụ: `3.6%`).
- Điều này tạo ra sự mâu thuẫn trực quan vì toán học `8.2M` trên giới hạn `2.0M` đáng lẽ phải vượt quá 410%, chứ không phải 3.6%.

## 3. Root Cause
- Trong tệp giao diện [webview.html](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/resources/webview.html#L1405), trường cập nhật cho phần hiển thị token đang gọi `wf.total_tokens` (tổng tích lũy toàn bộ các lượt giao thoại) thay vì `wf.active_tokens` (lượng token trong cửa sổ ngữ cảnh hoạt động hiện tại).
- Do thanh tiến độ và tỷ lệ phần trăm được tính toán dựa trên `active_tokens` (để so sánh với giới hạn ngữ cảnh `2.0M` của mô hình), việc hiển thị `total_tokens` ở nhãn số lượng đã tạo ra sự lệch pha này.

## 4. Scope
- **In Scope**:
  - Sửa đổi tệp `extensions/visualizer/resources/webview.html` để hiển thị `wf.active_tokens` (nếu không có thì fallback về `wf.total_tokens`) tại nhãn số lượng token của Workflow.
  - Chạy lệnh `node build.js` để tạo lại tệp `src/webviewHtml.ts`.
  - Biên dịch lại extension.
- **Out of Scope**: Không thay đổi logic backend đếm token hay cơ sở dữ liệu.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [webview.html](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/resources/webview.html) | Thay đổi trường hiển thị thành `active_tokens` |

## 6. Proposed Fix
Thay đổi dòng số 1405 trong `webview.html`:
```javascript
-                    document.getElementById("workflow-usage-tokens-total").innerText = formatTokens(wf.total_tokens);
+                    document.getElementById("workflow-usage-tokens-total").innerText = formatTokens(wf.active_tokens || wf.total_tokens);
```

## 7. Risks
- **Risk**: Một số phiên cũ không lưu `active_tokens` trong SQLite có thể hiển thị rỗng. → **Mitigation**: Thêm fallback `wf.active_tokens || wf.total_tokens` để nếu không có `active_tokens`, giao diện vẫn hiển thị `total_tokens` như cũ.

## 8. Acceptance Criteria
- [ ] Nhãn số lượng token hiển thị đúng lượng token hoạt động hiện tại (ví dụ: `56.3K / 2.0M tokens`), khớp hoàn toàn với tỷ lệ phần trăm hiển thị ở bên phải (ví dụ: `2.81%`).
- [ ] Giao diện hoạt động trơn tru sau khi biên dịch lại extension.

## 9. Test Plan
- **Verification**: Biên dịch extension bằng lệnh `make compile` trong thư mục `extensions/visualizer/`.
- **Manual Check**: Kiểm tra trực quan xem nhãn text hiển thị có khớp với phần trăm hay không.
