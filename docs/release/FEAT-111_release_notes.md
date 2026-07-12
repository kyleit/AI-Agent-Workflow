# Release Notes — FEAT-111 Hierarchical Multi-Agent Runtime (v6.10.0)

Bản ghi nhận các cải tiến và cập nhật quan trọng của phiên bản v6.10.0.

## 1. Các cải tiến chính
- **Bộ điều phối phân cấp đa tác nhân**: Triển khai `hierarchical_runtime.py` phân cấp rõ vai trò `orchestrator`, `supervisor`, `subagent`.
- **Lập lịch song song thực sự**: Thiết lập concurrency limit linh hoạt, quản lý xếp hàng công việc phi block qua Command Inbox.
- **Worker Isolation & Heartbeats**: Tách biệt tiến trình các tác nhân con, đo dấu hiệu sống định kỳ ngăn ngừa treo luồng.
- **An toàn khoá (Lock Manager)**: Chặn đứng các hành vi ghi đè tài nguyên chéo thư mục hoặc xung đột file trong chạy song song.
- **Uỷ quyền thời gian thực hạn chế**: Tích hợp `authorization.json` tự động hết hạn, đảm bảo an ninh cho luồng làm việc.
