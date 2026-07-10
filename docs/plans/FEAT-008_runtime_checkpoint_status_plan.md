<!-- File path: docs/plans/FEAT-008_runtime_checkpoint_status_plan.md -->

# Kế hoạch triển khai - Trạng thái Checkpoint Runtime (in_progress / completed / failed)

Chào Ba, đây là bản kế hoạch lưu trong dự án để tích hợp trường `"status"` vào phiên bản trạng thái Runtime Checkpoint.

## 1. Mục tiêu
- **Theo dõi trạng thái chi tiết**: Phân biệt giữa bước đã hoàn thành (`completed`) và bước đang thực thi dở dang (`in_progress`).
- **Nâng cấp cơ chế Resume**: Giúp khôi phục chính xác bước bị gián đoạn thay vì chỉ khôi phục từ checkpoint đã hoàn tất trước đó.

## 2. Các thay đổi chi tiết
- **skills/workflow-runtime/SKILL.md**: Định nghĩa trường `"status"` vào cấu trúc của `.session.json`.
- **skills/resume-workflow/SKILL.md** & **skills/software-development-workflow/SKILL.md**: Tích hợp đọc/hiển thị trạng thái `"status"`.
- **CHANGELOG.md**: Bumps phiên bản lên 2.8.0.

## 3. Kế hoạch kiểm tra
- Chạy `aiwf doctor` kiểm tra tính tương thích.
