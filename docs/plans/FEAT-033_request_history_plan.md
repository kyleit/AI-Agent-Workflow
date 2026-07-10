<!-- File path: docs/plans/FEAT-033_request_history_plan.md -->

---
feature_id: FEAT-033
feature_name: Request History System
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-033_request_history.md
next_artifact: ../designs/FEAT-033_request_history_blueprint.md
---

# FEAT-033: Request History System

## Objective
- **Business Objective**: Cung cấp khả năng kiểm toán (audit) cho từng yêu cầu gọi provider/model LLM đơn lẻ được thực hiện trong suốt quá trình hoạt động của AIWF. Giúp Ba trả lời ngay câu hỏi: "Yêu cầu nào tiêu tốn nhiều token nhất, chi phí nhiều nhất, thời gian chạy lâu nhất và hoạt động tool call nhiều nhất?".
- **Expected Outcome**: Ba có thể theo dõi danh sách lịch sử yêu cầu chi tiết dạng dòng thời gian và chọn xem chi tiết từng request (metadata, tool calls, context breakdown cụ thể của request đó) qua cả CLI và bảng điều khiển Visualizer.

## Scope

### Included
- Thiết kế di trú (migration) cơ sở dữ liệu SQLite thêm bảng `provider_requests` mới và các chỉ mục tương ứng để truy vấn nhanh.
- Thiết lập dịch vụ ghi nhận request phía backend bảo đảm ghi nhận chính xác 1 lần, chống trùng lặp dữ liệu khi chạy lại đồng bộ.
- Xây dựng lệnh CLI và API truy vấn dữ liệu từ SQLite để trả về cho Visualizer.
- Thiết kế giao diện Visualizer mới: Panel Lịch sử yêu cầu (Request History) dạng Timeline và panel Chi tiết yêu cầu (Request Detail View).
- Hỗ trợ lọc (filter) và sắp xếp (sort) các yêu cầu theo các trường thông số chính.

### Excluded
- Không tính toán và lưu trữ lịch sử yêu cầu trực tiếp bên trong giao diện Webview.
- Không thực hiện tối ưu hóa prompt hay tự động nén context tự động trong phase này (sẽ làm ở các phase sau).

## Project Impact
- **Database**: `project_runtime.db` (bổ sung bảng `provider_requests` và chỉ mục).
- **Backend CLI**: `workflow_runtime.py` (tích hợp lệnh truy vấn chi tiết).
- **Frontend Extension**: Webview hiển thị giao diện audit request timeline/details.

## Dependencies
- Khung sườn lưu trữ SQLite hiện có.
- Trạng thái Context Breakdown đã hoàn thành từ Phase 1.

## Risks
- **Rủi ro**: Khối lượng request tăng lên làm phình to dung lượng DB hoặc làm giảm hiệu suất truy vấn.
  - *Giảm thiểu*: Thiết lập chỉ mục phù hợp trên các trường thường xuyên lọc/sắp xếp (`project_id`, `workflow_id`, `created_at`, `total_tokens`, `cost_usd`) để bảo đảm tốc độ truy vấn dưới 100ms.
- **Rủi ro**: Dữ liệu request bị trùng lặp khi chạy đồng bộ trạng thái nhiều lần.
  - *Giảm thiểu*: Sử dụng ràng buộc UNIQUE cho cột `request_id` kết hợp câu lệnh `INSERT OR IGNORE` ở tầng SQLite.

## Acceptance Criteria
- [ ] Bảng `provider_requests` được di trú thành công trong SQLite mà không làm mất mát dữ liệu cũ.
- [ ] CLI truy vấn `usage requests` chạy chính xác và xuất dữ liệu dạng bảng/JSON đầy đủ.
- [ ] Giao diện Webview có panel Request History timeline và detail view liên kết chính xác với thông tin Context Breakdown.
- [ ] Không có bản ghi request nào bị trùng lặp khi re-sync.
- [ ] Sắp xếp và bộ lọc hoạt động chính xác.

## Deliverables
- Tệp tin SQL Migration tạo bảng `provider_requests` và chỉ mục.
- Logic thu thập request LLM phía backend.
- CLI truy vấn và API giao tiếp dữ liệu.
- Các component hiển thị giao diện trên Webview.
- Bộ automated unit tests bao phủ 12 kịch bản yêu cầu.

## Estimated Complexity
- **Medium**: Đòi hỏi sửa đổi cả tầng lưu trữ SQLite, logic CLI Python, và tầng giao diện TypeScript Webview nhưng cấu trúc dữ liệu đã được định hình rõ ràng từ Phase 1.

## Recommended Blueprint Focus
- Tập trung vào thiết kế schema cơ sở dữ liệu `provider_requests` chi tiết với các ràng buộc duy nhất và chỉ mục tối ưu.
- Thiết kế luồng truyền nhận dữ liệu từ SQLite thông qua Webview Provider mà không làm tăng độ trễ hoạt động.

## Recommended Next Skill
/blueprint
