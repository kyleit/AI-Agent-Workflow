<!-- File path: docs/designs/FIX-022_fix_token_diff_select_flickering_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-022
workflow: quick-fix
status: approved
---
# Technical Design Blueprint – Fix Token Diff Select Flickering

## 1. Proposed Code Changes

### `extensions/visualizer/resources/webview.html`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật logic Javascript để ngăn chặn việc ghi đè nội dung `innerHTML` của bộ chọn khi không có sự thay đổi hoặc phần tử đang được người dùng click chọn (focused).
- **Changes**:
  - Tại đoạn gán `selA.innerHTML = optionsHtml;` và `selB.innerHTML = optionsHtmlB;`:
  - Thay thế bằng logic kiểm tra:
    ```javascript
    const isFocusedA = document.activeElement === selA;
    const isFocusedB = document.activeElement === selB;

    if (!isFocusedA && selA.innerHTML !== optionsHtml) {
        selA.innerHTML = optionsHtml;
        selA.value = prevValA;
    }
    if (!isFocusedB && selB.innerHTML !== optionsHtmlB) {
        selB.innerHTML = optionsHtmlB;
        selB.value = prevValB;
    }
    ```

### `extensions/visualizer/src/webviewHtml.ts`
- **Operation**: MODIFY (Auto-generated)
- **Responsibility**: Chứa giao diện được biên dịch lại của `webview.html`.
- **Changes**: Được cập nhật tự động bằng lệnh `node build.js`.

## 2. Target Folder Structure
```text
.
├── docs
│   ├── issues
│   │   └── FIX-022_fix_token_diff_select_flickering.md
│   └── designs
│       └── FIX-022_fix_token_diff_select_flickering_blueprint.md
└── extensions
    └── visualizer
        ├── resources
        │   └── webview.html
        └── src
            └── webviewHtml.ts
```

## 3. Interface & Data Contracts
- Không thay đổi API/CLI hay Schema.

## 4. Algorithms & Key Logic
- So sánh thuộc tính `innerHTML` hiện tại với chuỗi HTML mới (`optionsHtml`).
- Sử dụng `document.activeElement` để xác định xem phần tử `<select>` có đang hoạt động (được click chọn) hay không. Chỉ cập nhật khi không ở trạng thái active và có sự khác biệt dữ liệu.

## 5. Validation Rules
- Đảm bảo giữ lại thuộc tính `value` cũ của bộ chọn sau khi cập nhật `innerHTML`.

## 6. Implementation Checklist
- [ ] Thay đổi mã nguồn Javascript trong `extensions/visualizer/resources/webview.html`.
- [ ] Chạy lệnh `node build.js` trong thư mục `extensions/visualizer` để biên dịch sang `webviewHtml.ts`.
- [ ] Kiểm tra trực quan trên Visualizer dashboard để xác nhận không còn hiện tượng chớp tắt.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Bấm vào bộ chọn `diff-select-a` và `diff-select-b` không làm biến mất dropdown list.
  - *REQ-002*: Khi danh sách yêu cầu thay đổi (có request mới), bộ chọn tự động cập nhật danh sách option mới sau khi người dùng click ra ngoài (unfocus).
