# Technical Blueprint – Fix Dashboard Navigation Bar (FEAT-042)
 
---
artifact_type: blueprint
feature_id: FEAT-042
workflow: standard
status: approved
---
 
## 1. File-by-File Analysis & Proposed Mutations
 
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Tái cấu trúc CSS Tab Navigation từ inline styles thành lớp CSS, thiết lập khoảng cách an toàn, nâng font size lên 11px. Cập nhật JS logic khởi tạo lắng nghe sự kiện không đồng bộ, loại bỏ ràng buộc DOMContentLoaded cứng nhắc. | None | Thấp. Toàn bộ logic giao diện chạy độc lập. |
| `extensions/visualizer/src/webviewHtml.ts` | `REBUILD` | Tệp biên dịch tự động từ `webview.html` thông qua `node build.js`. | `webview.html` | Thấp. Được quản lý bởi build pipeline. |
 
---
 
## 2. Visual & Interaction Specifications
 
### 📐 Layout & Spacing
- **Container Margins**: `margin: 12px 12px 16px 12px;` tách biệt hoàn toàn khỏi block Gauges ở trên và block Scroll ở dưới.
- **Container Spacing (Gap)**: `gap: 4px;` tạo khoảng hở thẩm mỹ giữa các tab.
- **Button Padding**: `padding: 8px 2px;` gia tăng diện tích click target.
- **Click Target Target Size**: Chiều cao nút tối thiểu `min-height: 36px` đạt chuẩn tương tác công thái học VS Code.
 
### 🎨 Styling & Typography
- **Background Color**: `rgba(16, 25, 42, 0.7)` nền mờ mờ cao cấp.
- **Border**: `1px solid rgba(70, 142, 255, 0.15)` nét viền mảnh tinh tế.
- **Font Size**: `font-size: 11px;` rõ nét, dễ đọc.
- **Font Weight**: `600` nét bán đậm chữ hoa (`text-transform: uppercase;`).
 
### ⚡ Navigation States
1. **Default (Chưa kích hoạt)**:
   - Màu chữ: `var(--muted)` (#8ba4bd).
   - Nền: `transparent`.
2. **Hover (Rê chuột)**:
   - Màu chữ: `var(--text)` (#eaf6ff).
   - Nền: `rgba(255, 255, 255, 0.04)`.
3. **Active (Đang kích hoạt)**:
   - Màu chữ: `#ffffff` sắc nét trên nền sáng.
   - Nền: `var(--blue)` (#2f8cff) nổi bật.
   - Hiệu ứng đổ bóng: `box-shadow: 0 2px 4px rgba(47, 140, 255, 0.3)`.
4. **Focus-visible (Duyệt bàn phím)**:
   - Border phát sáng: `box-shadow: 0 0 0 2px var(--cyan)`.
 
---
 
## 3. Keyboard & Accessibility (A11y)
- Thiết lập `role="tablist"` cho container.
- Mỗi nút tab gắn `role="tab"`.
- Tab hiện tại nhận thuộc tính `aria-selected="true"`. Các tab khác nhận `aria-selected="false"`.
- Bổ sung chỉ thị liên kết vùng nội dung bằng thuộc tính `aria-controls="[id-panel-tương-ứng]"`.
 
---
 
## 4. Algorithms & Logic Specifications
 
### DOM Initialization Strategy
Để khắc phục lỗi `DOMContentLoaded` bị trôi qua trước khi script của webview thực thi:
```javascript
function initTabs() {
    // 1. Gắn sự kiện click close-token-diff
    // 2. Gắn sự kiện click tabButtons chuyển đổi panel hiển thị, cập nhật class active và thuộc tính aria-selected.
}
 
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
} else {
    initTabs();
}
```
 
---
 
## 5. Verification Plan
 
### Manual Verification
- Thực hiện đóng gói và kiểm tra click chuyển đổi giữa các Tab: **Workflow**, **Insights**, **Timeline**, **Budget**, **Context**, **Optimize**.
- Xác nhận không có tab nào không hoạt động hoặc không đổi trạng thái hiển thị.
