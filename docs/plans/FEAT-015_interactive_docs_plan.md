# Implementation Plan - FEAT-015: Interactive Docs & Workflow Simulator Website

## Goal Description
Xây dựng một trang web tài liệu tĩnh (HTML/CSS/JS) tích hợp đầy đủ thông tin chi tiết của 19 skills (bỏ OKR generator), hướng dẫn sử dụng chi tiết theo 3 luồng workflow chính (Standard, Quick Feature, Quick Fix), cùng với các công đoạn vận hành runtime. Trang web sẽ tích hợp **Interactive Simulator** để người dùng trải nghiệm thực tế quy trình và có thể được deploy trực tiếp lên GitHub Pages thông qua thư mục `docs/`.

---

## Design System & Style Tokens (From Visualizer Extension)
Để đồng bộ 100% với giao diện Visualizer Extension hiện tại, chúng ta sẽ áp dụng các Tokens sau:
*   **Colors**:
    *   `--bg`: `#060b14` (Background nền tối)
    *   `--panel`: `rgba(13, 20, 34, 0.78)` (Glassmorphism card)
    *   `--line`: `rgba(70, 142, 255, 0.22)` (Đường biên neon nhạt)
    *   `--cyan`: `#00e5ff` (Accent màu chính cho liên kết, highlight)
    *   `--blue`: `#2f8cff` (Màu chính phụ)
    *   `--purple`: `#a66cff` (Màu bổ trợ gradient)
    *   `--green`: `#5cff75` (Trạng thái PASS / Thành công)
    *   `--red`: `#ff4d7a` (Trạng thái FAIL / Cảnh báo)
*   **Background Effects**:
    *   Glow gradient: Tích hợp 2 điểm sáng radial ở 10% góc trái và 92% góc phải kết hợp liner gradient nền tối.
    *   Lớp phủ lưới Grid-lines CSS ở nền (`background-size: 28px 28px`).
*   **Typography**:
    *   Phông chữ: `Inter, ui-sans-serif, system-ui`.
    *   Tỷ lệ font: `1.2` (Dense UI) cho các thông tin thẻ chi tiết của skill và `1.4` cho phần văn bản hướng dẫn để tăng tính thoáng mắt.
*   **UX Laws Applied**:
    *   *Hick's Law*: Phân nhóm 19 skills thành 5 danh mục (workflow, memory, environment, architecture, runtime) thông qua các nút filter động thay vì hiển thị tràn lan.
    *   *Doherty Threshold*: Simulator phản hồi tức thời (<100ms) with các hiệu ứng chuyển đổi mượt mà để mang lại trải nghiệm điều hướng mượt như ứng dụng native.

---

## Proposed Changes

### Documentation & Assets

#### [NEW] [index.html](../../interactive-docs/index.html)
File cấu trúc HTML chính của trang tài liệu. Sử dụng bố cục Sidebar điều hướng kết hợp với nội dung Dynamic Tab.

#### [NEW] [style.css](../../interactive-docs/docs-assets/style.css)
Hệ thống CSS hiện đại kế thừa toàn bộ biến màu CSS và phông nền của Visualizer extension. Tích hợp hiệu ứng thanh cuộn Neon scrollbar phát sáng, border mỏng sáng, đổ bóng sâu.

#### [NEW] [skills-data.js](../../interactive-docs/docs-assets/skills-data.js)
Dữ liệu chi tiết của 19 skills (sau khi lọc bỏ OKR generator) được tổ chức thành mảng JSON. Mỗi skill chứa: lệnh, Checkpoint, vai trò, input/output, best practice.

#### [NEW] [app.js](../../interactive-docs/docs-assets/app.js)
Logic vận hành website:
*   **Routing**: Chuyển đổi mượt mà giữa các tab lớn (Tổng quan, Hướng dẫn Workflow, Thư mục Skills, Giả lập Simulator, Vận hành Runtime).
*   **Search & Filter**: Tìm kiếm skill theo tên/lệnh, lọc theo category.
*   **Workflow Simulator**: Trình mô phỏng quy trình tương tác. Người dùng có thể click chọn "Standard", "Quick Feature" hoặc "Quick Fix", sau đó bấm nút "Tiếp tục" qua từng bước để xem CLI hiển thị gì, Agent làm gì và lập trình viên cần duyệt gì.

---

## Verification Plan

### Manual Verification
1. Mở trực tiếp file [index.html](../../interactive-docs/index.html) trên trình duyệt Chrome/Safari để kiểm tra giao diện và độ responsive.
2. Kiểm tra tính năng chuyển tab và hiệu ứng animation.
3. Test tính năng tìm kiếm skill (ví dụ: gõ "sync" hoặc "release" để xem kết quả lọc).
4. Chạy giả lập (Simulator) các bước của Standard, Quick Feature, Quick Fix để đảm bảo các câu lệnh CLI hiển thị chính xác.
