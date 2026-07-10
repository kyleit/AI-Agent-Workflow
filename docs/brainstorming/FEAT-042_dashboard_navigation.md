# Brainstorming – Fix AIWF Dashboard Navigation Bar (FEAT-042)
 
| 🔒 DISCOVERY MODE ACTIVE |
| :--- |
| This Skill is running in **READ-ONLY / DISCOVERY ONLY** mode. |
| I will **NOT** modify any source code. |
| I will **NOT** edit any project files. |
| I will **NOT** implement anything. |
| I will **ONLY** perform Requirement Discovery. |
| The ONLY file I may write is: `docs/brainstorming/FEAT-XXX_feature_name.md` |
| And ONLY after explicit user confirmation (Y/N). |
 
---
 
## 1. UX Audit Report
 
### Current Visual Attachment
- **Issue**: Thanh điều hướng (Navigation Bar) được đặt sát sườn với khối đo lường Context Gauge ở trên và Stepper-Scroll ở dưới (khoảng cách 0px), làm cho giao diện bị dính liền và không phân định rõ ràng các khu vực chức năng.
- **Audited Solution**: Cần tách biệt thanh điều hướng ra thành một khối container độc lập. Đưa khoảng cách lề trên (margin-top) lên `12px` và lề dưới (margin-bottom) lên `16px`.
- **UX Recommendation**: Sử dụng kỹ thuật viền phát sáng (neon line borders) và đổ bóng nhẹ (box-shadow) để nâng nổi thanh điều hướng lên trên bề mặt nền, tạo cảm giác trực quan 3D chiều sâu (depth hierarchy).
 
---
 
## 2. Layout Analysis
 
- **Margin/Padding**: Hiện tại container sử dụng lề inline `margin: 0 12px 8px 12px` khiến nó dính chặt vào block phía trên. Padding chỉ đạt `2px` làm cho nút bấm quá nhỏ hẹp.
- **Hierarchy**: Container của navigation hiện nằm xen kẽ giữa header sticky và vùng cuộn step-scroll.
- **Flex/Grid**: Phân chia `flex: 1` cho các nút bấm là chuẩn xác nhưng thiếu khoảng trống giữa các nút (gap).
- **Solution Proposal**: Thiết lập cấu trúc CSS lớp ngoài mới `.tab-nav-container` sử dụng `background: rgba(16, 25, 42, 0.7)` và `.tab-nav-btn` với padding lớn hơn (`8px 2px`) và có gap `4px` để tăng khoảng trống bấm chạm.
 
---
 
## 3. Typography Review
 
- **Font Size**: Font size hiện tại của các nút tab chỉ có `7px` — kích thước này quá nhỏ đối với mọi màn hình độ phân giải thông thường, vi phạm các nguyên tắc công thái học (ergonomic).
- **Touch/Click Target**: Chiều cao thực tế của nút chỉ khoảng ~19px, khó bấm trúng và dễ gây mỏi mắt.
- **Target Typography**: Nâng kích thước chữ lên `11px` (hoặc `10.5px`), font weight `600`, chiều cao tối thiểu của khu vực bấm (min-height) đạt `36px` để tối ưu hóa khả năng tương tác bằng cả chuột lẫn màn hình cảm ứng.
 
---
 
## 4. Navigation Architecture Review
 
- **The DOMContentLoaded Bug (Root Cause)**: Toàn bộ code gắn sự kiện `addEventListener("click")` cho các tab hiện đang bị bọc trong listener `DOMContentLoaded`. Vì Visualizer webview tải script không đồng bộ sau khi DOM đã được load xong, sự kiện `DOMContentLoaded` đã được kích hoạt từ trước đó, khiến khối đăng ký sự kiện chuyển tab **không bao giờ được chạy**.
- **Fix**: Viết hàm `initTabs()` độc lập và chạy kiểm tra `document.readyState`. Nếu DOM đã sẵn sàng (interactive/complete) thì gọi hàm khởi tạo ngay lập tức.
- **Routing**: Đồng bộ lệnh gọi `vscode.postMessage` cho từng tab tương ứng (`GET_RUNTIME_INSIGHTS`, `GET_TIMELINE_DATA`, `GET_BUDGET_DATA`, `GET_CONTEXT_REBUILDER_DATA`, `GET_OPTIMIZER_DATA`) để nạp động dữ liệu tương thích.
 
---
 
## 5. Accessibility Report
 
- **Tablist Role**: Bổ sung thuộc tính `role="tablist"` cho container.
- **Tab Buttons**: Bổ sung `role="tab"`, `aria-selected="true/false"`, `aria-controls="[id-panel]"`.
- **Focus Indicator**: Thiết lập `:focus-visible` tạo đường viền xanh cyan sáng (`box-shadow: 0 0 0 2px var(--cyan)`) để hỗ trợ duyệt bằng bàn phím (tab navigation).
 
---
 
## 6. Gap Analysis (Bảng phân tích khoảng cách)
 
| Yêu cầu thiết kế | Hiện trạng | Khoảng cách cần vá |
| :--- | :--- | :--- |
| **Khoảng cách lề** | 0px lề trên, dính liền | margin-top `12px`, margin-bottom `16px` |
| **Kích thước font** | `7px` siêu nhỏ | Tăng lên `11px`, font-weight `600` |
| **Tương tác click**| Bị chết cứng do bug DOMContentLoaded | Khởi tạo qua check `readyState` |
| **Chỉ thị Active** | Chỉ đổi màu chữ nhạt | Dùng nền màu `var(--blue)` nổi bật |
| **Accessibility** | Không có ARIA roles | Thêm `role="tab"`, `aria-selected` |
 
---
 
## 7. Solution Options
 
### Option A: Refactor inline styles thành các CSS class trong Style block (Khuyên dùng)
- **Advantages**: Cực kỳ dễ bảo trì, tách biệt hoàn toàn giữa cấu trúc (HTML) và phong cách (CSS). Hỗ trợ hover/active/focus mượt mượt.
- **Complexity**: Low
- **Performance**: High
 
### Option B: Sửa đổi trực tiếp inline styles bằng Javascript
- **Advantages**: Tác động cục bộ.
- **Disadvantages**: Code HTML trở nên hỗn loạn, khó viết hover/focus states.
- **Complexity**: Medium
 
---
 
## 8. User Confirmation Gate

────────────────────────────────────────────────────
Requirement Discovery Complete

Feature:                  Fix Navigation System (FEAT-042)
Recommended Solution:     Option A — Refactor to custom CSS classes with readyState trigger

Continue generating Brainstorming document?

  [Y] Yes — Generate docs/brainstorming/FEAT-042_dashboard_navigation.md
  [N] No  — Stop.
────────────────────────────────────────────────────
