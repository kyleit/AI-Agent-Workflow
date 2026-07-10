<!-- File path: docs/plans/FEAT-023_aiwf_project_registry_and_global_update_plan.md -->

---
feature_id: FEAT-023
feature_name: Project Registry & Global Update CLI
status: reviewed
stage: planning
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../brainstorming/FEAT-023_aiwf_project_registry_and_global_update.md
next_artifact: ../designs/FEAT-023_aiwf_project_registry_and_global_update_blueprint.md
---

# FEAT-023: Project Registry & Global Update CLI

## Objective
- Triển khai cơ chế quản lý dự án tập trung (Project Registry) cho CLI `aiwf` giúp dễ dàng theo dõi toàn bộ các thư mục dự án đã cài đặt AI Skill Framework trên máy.
- Cung cấp khả năng cập nhật đồng loạt toàn bộ các dự án này thông qua câu lệnh `aiwf update --all`, giảm thiểu thao tác thủ công, tránh bỏ sót và tối ưu hóa thời gian bảo trì hệ thống.

## Scope
### Included
- Thiết lập tệp cấu hình registry JSON toàn cục chuẩn OS AppData (`projects.json`).
- Tự động ghi nhận và đăng ký dự án mới khi thực hiện `aiwf install` thành công.
- CLI hỗ trợ lệnh `aiwf register [--path <path>] [--force]` để đăng ký thủ công dự án cũ.
- Hỗ trợ các lệnh con quản lý registry: `aiwf list`, `aiwf unregister`, `aiwf registry doctor`, `aiwf registry cleanup`.
- Nâng cấp lệnh cập nhật hỗ trợ hai chế độ:
  - `aiwf update --current` (hoặc mặc định): Cập nhật cho dự án hiện tại.
  - `aiwf update --all`: Cập nhật tuần tự cho mọi dự án đang hoạt động trong registry. Ghi nhận lỗi riêng lẻ và kết xuất Summary Report.
- Thực hiện cơ chế ghi đè JSON nguyên tử (atomic write) an toàn và khôi phục tự động nếu tệp JSON bị hỏng.
- Đảm bảo tương thích đa nền tảng (macOS, Linux, Windows PowerShell/CMD).

### Excluded
- Không hỗ trợ cập nhật song song (parallel update) các dự án trong registry để tránh xung đột I/O trên đĩa.
- Không tự động đăng ký các dự án khi chưa chạy `install` hoặc `register`.
- Không gửi thông tin hoặc lưu trữ metadata dự án lên bất kỳ server remote nào (100% dữ liệu registry nằm cục bộ trên máy lập trình viên).

## Project Impact
- **Modules & CLI**: Nâng cấp các file CLI wrappers shell (`install.sh/ps1`, `update.sh/ps1`, `doctor.sh/ps1`) và tệp Python điều phối chính (`workflow_runtime.py`).
- **State & Database**: Không ảnh hưởng đến dữ liệu SQLite cục bộ của từng dự án riêng lẻ.
- **Config**: Tạo thêm tệp registry tĩnh cục bộ trên hệ thống.

## Dependencies
- **Python 3.x**: Phải có sẵn trên hệ thống để thực thi script logic của registry.
- **Git CLI**: Cần thiết để các dự án được xác định root path và version tag.

## Risks
- **Path Case-Sensitivity (Windows/macOS)**:
  - *Nguy cơ*: So sánh đường dẫn hoa/thường không chuẩn xác dẫn đến việc lưu trùng lặp dự án.
  - *Giảm thiểu*: Sử dụng hàm chuẩn hóa đường dẫn tuyệt đối (`os.path.realpath`) và so sánh không phân biệt chữ hoa chữ thường trên Windows.
- **Registry File Corruption**:
  - *Nguy cơ*: File registry bị ghi đè dở dang khi bị ngắt tiến trình đột ngột, dẫn đến hỏng cấu trúc JSON.
  - *Giảm thiểu*: Ghi file nguyên tử (ghi ra `.tmp` rồi rename) kết hợp cơ chế backup tự động khôi phục nếu lỗi cú pháp xảy ra.
- **Batch Update Failures**:
  - *Nguy cơ*: Lỗi cập nhật tại một dự án (như thiếu quyền write, mất thư mục gốc) làm dừng đột ngột toàn bộ tiến trình cập nhật của các dự án còn lại.
  - *Giảm thiểu*: Đóng gói logic cập nhật của từng dự án trong khối `try/except` độc lập, ghi nhận lỗi và tiếp tục dự án tiếp theo.

## Acceptance Criteria
- [ ] Lệnh `aiwf install` hoàn thành và tự động đăng ký dự án vào `projects.json`.
- [ ] Lệnh `aiwf register` hoạt động chính xác cho dự án đã cài framework cũ, không ghi đè trùng lặp (idempotent).
- [ ] Lệnh `aiwf list` hiển thị bảng danh sách các dự án đã đăng ký, status, phiên bản rõ ràng.
- [ ] Lệnh `aiwf update --all` lặp qua tất cả các dự án trong registry và hoàn thành cập nhật, xuất ra báo cáo Summary tổng kết số lượng thành công/thất bại.
- [ ] Lệnh `aiwf registry cleanup` xóa hoặc đánh dấu missing các dự án có đường dẫn không tồn tại.
- [ ] CLI trên Windows (PowerShell/CMD) và Unix (Bash) đều hoạt động mượt mà.

## Deliverables
- Module Python mới `skills/workflow-runtime/scripts/aiwf_registry.py` chứa logic registry.
- CLI sub-commands mới được đăng ký trong `workflow_runtime.py`.
- Các file scripts cài đặt/cập nhật được cập nhật mượt mà.
- Unit/Integration tests cho registry helper.
- Tài liệu cập nhật đầy đủ (`README.md`, `CHANGELOG.md`, v.v.).

## Estimated Complexity
- **Medium**: Đòi hỏi kiểm tra đa nền tảng kỹ lưỡng, đặc biệt là xử lý chuẩn hóa đường dẫn trên Windows và Unix, đảm bảo cơ chế ghi nguyên tử an toàn tuyệt đối.

## Recommended Blueprint Focus
- Tập trung thiết kế cơ chế lưu trữ JSON nguyên tử (atomic write) và phương án xác định đường dẫn AppData tối ưu cho từng hệ điều hành.
- Thiết kế chi tiết cấu trúc JSON Schema cho tệp registry, đảm bảo khả năng tương thích ngược và tự động khôi phục dữ liệu khi tệp bị hỏng.

## Recommended Next Skill
/blueprint
