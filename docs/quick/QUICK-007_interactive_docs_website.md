<!-- File path: docs/quick/QUICK-007_interactive_docs_website.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-007
workflow: quick-feature
status: completed
---
# Mini Feature Specification – Interactive Docs & Workflow Simulator Website

## 1. Feature Goal
Xây dựng một trang web tài liệu tĩnh (HTML/CSS/JS) chạy Client-side, tích hợp đầy đủ thông tin của 19 skills (sau khi loại bỏ OKR generator), hướng dẫn sử dụng chi tiết theo 3 quy trình chính (Standard Workflow, Quick Feature, Quick Fix), cùng với các hướng dẫn vận hành runtime. Trang web được thiết kế kế thừa 100% phong cách thẩm mỹ của Visualizer Extension và tích hợp bộ giả lập Simulator trực quan cho phép người dùng trải nghiệm thực tế quy trình SDLC. Website được lưu trữ trực tiếp trong thư mục `interactive-docs/` để tự động kích hoạt trên GitHub Pages.

## 2. Scope

- **In Scope**:
  - Tạo trang giao diện chính tại `interactive-docs/index.html` sử dụng bố cục Sidebar hiện đại và các tab nội dung động.
  - Tạo tệp phong cách `interactive-docs/docs-assets/style.css` áp dụng các biến màu sắc, background radial-gradient, Grid-lines và scrollbar phát sáng của Visualizer extension.
  - Tạo tệp cơ sở dữ liệu `interactive-docs/docs-assets/skills-data.js` chứa thông tin chi tiết of 19 skills (mục đích, Checkpoint, vai trò, input/output, mẹo sử dụng).
  - Tạo tệp xử lý logic `interactive-docs/docs-assets/app.js` để hỗ trợ tìm kiếm/lọc các skills và vận hành **Interactive Workflow Simulator** (mô phỏng từng bước nhập lệnh CLI và gác duyệt của 3 quy trình).
  - Đồng bộ kế hoạch thực thi `FEAT-015_interactive_docs_plan.md` vào thư mục `docs/plans/` của dự án.
  
- **Out of Scope**:
  - Tích hợp Database hoặc Server Backend.
  - Sửa đổi lõi của Python CLI runtime engine hoặc mã nguồn của extension Visualizer.
  - Hỗ trợ các trình duyệt rất cũ (chỉ tập trung tối ưu hóa cho Chrome/Safari/Firefox hiện đại).
