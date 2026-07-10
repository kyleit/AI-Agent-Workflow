<!-- File path: docs/plans/FEAT-011_session_usage_plan.md -->

---
feature_id: FEAT-011
feature_name: Update Extension UI with Full Session Token & Cost Metrics
status: draft
stage: planning
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: None
next_artifact: ../designs/FEAT-011_session_usage_blueprint.md
---

# Project Plan – Session Usage Panel & Metrics in VSCode Visualizer Extension

Bản kế hoạch quản lý dự án tích hợp khối dữ liệu Session Usage vào Visualizer Extension thưa Ba.

## 1. Mục tiêu dự án
*   **Mục tiêu chính**: Cập nhật giao diện Visualizer Sidebar Extension để hiển thị chính xác lượng token tiêu thụ và chi phí ước tính của toàn bộ phiên chạy từ tệp cấu hình `.agents/.session.json`.
*   **Mục tiêu chất lượng**: Thiết kế tối giản, trực quan (theo đúng hướng dẫn của `frontend-design`), hỗ trợ đầy đủ thanh tiến trình màu động và các trường hợp dự phòng khi thiếu dữ liệu (empty states).

## 2. Phạm vi thực hiện (Scope & Boundaries)
*   **Nằm trong phạm vi**:
    *   Sửa đổi tệp `extension.ts` để đọc và bảo toàn đối tượng `context_usage` trong tệp JSON.
    *   Bổ sung thẻ hiển thị `Session Usage` trong tệp `webviewHtml.ts` ngay dưới tệp session card.
    *   Viết CSS cho thẻ hiển thị mới và thanh tiến trình có 3 trạng thái màu (Xanh lá < 60%, Vàng 60%-85%, Đỏ > 85%).
    *   Tích hợp các hàm định dạng hiển thị thông minh trong Javascript của Webview.
    *   Biên dịch và đóng gói thử nghiệm extension.
*   **Nằm ngoài phạm vi**:
    *   Không thay đổi logic tính toán lượng token hoặc chi phí của Runtime Engine (mọi dữ liệu tính toán đều do Runtime ghi nhận vào session file trước đó).
    *   Không thiết kế lại toàn bộ extension (chỉ thêm mô-đun nhỏ).

## 3. Các đầu mục công việc & Các pha (Tasks & Milestones)
*   **Pha 1: Thiết kế kỹ thuật (Technical Blueprint)**
    *   Định nghĩa đặc tả HTML/CSS của thẻ `Session Usage`.
    *   Thiết kế chữ ký các hàm trợ giúp định dạng dữ liệu (`formatTokens`, `formatCost`, `formatPercentage`, v.v.).
*   **Pha 2: Phát triển & Biên dịch Extension**
    *   Sửa đổi tệp `extension.ts` và `webviewHtml.ts`.
    *   Chạy lệnh biên dịch TypeScript và đóng gói `vsce`.
*   **Pha 3: Kiểm duyệt & Nghiệm thu**
    *   Kiểm tra trực quan Webview hiển thị các chỉ số động.
    *   Xác minh các trường hợp trống hoặc lỗi dữ liệu không làm hỏng UI.

## 4. Rủi ro & Giải pháp giảm thiểu (Risks & Mitigations)
*   **Rủi ro 1: Lỗi crash giao diện Webview khi thiếu một vài trường dữ liệu trong JSON**
    *   *Giảm thiểu*: Thiết lập các fallback mặc định an toàn (`0`, `N/A`, `estimated`) cho mọi thuộc tính của đối tượng `context_usage`.
*   **Rủi ro 2: Thiết kế giao diện không đồng bộ với giao diện hiện tại của VSCode**
    *   *Giảm thiểu*: Sử dụng các biến CSS theme có sẵn (`var(--vscode-...)`) để đồng bộ màu sắc.

## 5. Kế hoạch kiểm duyệt chất lượng (Verification Plan)
*   [ ] Biên dịch TypeScript (`npm run compile` hoặc `make`) thành công không có lỗi.
*   [ ] Kiểm tra giao diện hiển thị trên VS Code Sidebar Panel chạy đúng đắn.
