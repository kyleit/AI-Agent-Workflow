<!-- File path: docs/designs/QUICK-007_interactive_docs_website_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-007
workflow: quick-feature
status: approved
---
# Technical Design Blueprint – Interactive Docs & Workflow Simulator Website

## 1. Proposed Code Changes

Tất cả các thay đổi dưới đây đều là thêm mới hoàn toàn các file tĩnh phục vụ cho Website trong thư mục `interactive-docs/`.

---

### [NEW] [index.html](../../interactive-docs/index.html)
*   **Bố cục cấu trúc**:
    *   `<aside>`: Sidebar điều hướng bên trái với logo AI Workflow, 5 liên kết chính (Tổng quan, Hướng dẫn Workflow, Thư mục 19 Skills, Vận hành Runtime, Trình giả lập SDLC).
    *   `<header>`: Tiêu đề động, thanh tìm kiếm skill nhanh và mô phỏng token usage bar.
    *   `<main>`: Vùng hiển thị nội dung động gồm 5 tab chuyển đổi ẩn/hiện tương ứng.
    *   `<section id="overview">`: SVG diagram luồng SDLC tiêu chuẩn + Giới thiệu framework.
    *   `<section id="workflows">`: Giao diện tab-in-tab so sánh 3 luồng (Standard, Quick Feature, Quick Fix) kèm nút sao chép nhanh câu lệnh.
    *   `<section id="skills">`: Bộ lưới Card hiển thị 19 skills. Bộ lọc nhanh theo 5 danh mục (workflow, memory, environment, architecture, runtime).
    *   `<section id="runtime">`: Hướng dẫn các lệnh CLI runtime kèm ví dụ cụ thể và nút copy.
    *   `<section id="simulator">`: Khung giả lập Terminal mô phỏng chạy CLI và gác duyệt.

---

### [NEW] [style.css](../../interactive-docs/docs-assets/style.css)
*   **Theme & Variable**:
    *   Đồng bộ hệ màu sắc và Radial Gradient nền tối từ `webview.html` của extension.
    *   Lớp phủ Grid-line nền CSS.
*   **Hiệu ứng & Hoạt ảnh**:
    *   Neon scrollbar phát sáng cho các khung nội dung dài.
    *   Hiệu ứng Hover Glassmorphism card (`background: rgba(13, 20, 34, 0.78)`, `backdrop-filter: blur(8px)`, `border: 1px solid rgba(70, 142, 255, 0.22)`).
    *   Hiệu ứng active glow chuyển tiếp mượt mà (<200ms).

---

### [NEW] [skills-data.js](../../interactive-docs/docs-assets/skills-data.js)
*   **Dữ liệu 19 Skills**: Tổ chức thành mảng JSON chứa các trường:
    *   `name`: Tên skill (ví dụ: `initialize-workflow`).
    *   `command`: Lệnh tương ứng (`/init`).
    *   `category`: Phân loại.
    *   `checkpoint`: Số checkpoint tương ứng trong SDLC.
    *   `purpose`: Mục đích chính.
    *   `input`/`output`: Các tham số đầu vào và sản phẩm đầu ra chính.
    *   `pitfall`: Lưu ý/lỗi thường gặp.

---

### [NEW] [app.js](../../interactive-docs/docs-assets/app.js)
*   **Điều hướng (Router)**: Lắng nghe sự kiện click menu sidebar để chuyển tab.
*   **Tìm kiếm & Bộ lọc**: Bộ lắng nghe sự kiện trên input tìm kiếm và nút filter để tự động render lại danh sách card skills tương ứng.
*   **Logic Giả lập (Simulator Engine)**:
    *   Quản lý trạng thái hiện tại (`currentStep`) cho 3 kịch bản: Standard, Feature, Fix.
    *   Khi click "Chạy CLI", giả lập in văn bản dòng lệnh ra Terminal giả lập.
    *   Khi click "Phê duyệt [Y/N]", giả lập in kết quả và chuyển bước kế tiếp của quy trình SDLC.

---

## 2. Test Plan

Vì đây là website tĩnh Client-side, kế hoạch kiểm thử sẽ tập trung vào tương tác người dùng:

### Manual Verification
1. Mở tệp [index.html](../../interactive-docs/index.html) trực tiếp trên các trình duyệt phổ biến (Chrome, Safari, Firefox) để kiểm tra giao diện hiển thị.
2. Kiểm tra tính năng tìm kiếm nhanh bằng cách nhập tên lệnh (ví dụ: "sync" hoặc "release") xem bộ lọc có cập nhật card lập tức hay không.
3. Chạy giả lập cả 3 kịch bản trên Simulator từ bước 1 đến bước cuối để kiểm tra độ chính xác của các câu lệnh CLI và kịch bản tương tác.
4. Kiểm tra tính năng copy lệnh nhanh trên các nút "Copy" xem nội dung trong Clipboard có chính xác không.
