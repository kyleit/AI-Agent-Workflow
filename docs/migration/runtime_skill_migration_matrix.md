# Skill Migration Matrix — Runtime Foundation v1

Bảng phân loại trạng thái di chuyển của các Skills hiện hành trong dự án.

| Skill Name | Status | Migration Action Required | Legacy Dependencies |
| :--- | :---: | :--- | :--- |
| **initialize-workflow** | Compatible | Đã di chuyển và tích hợp auto-start Resident Daemon. | None |
| **resume-workflow** | Compatible | Sử dụng `daemon.json` để kiểm tra trạng thái khôi phục. | None |
| **brainstorming** | Compatible | Gửi sự kiện báo cáo chéo Named Pipes. | None |
| **brainstorming-to-plan** | Compatible | Tải cấu trúc DAG thông qua SDK. | None |
| **plan-to-blueprint** | Compatible | Ghi nhận trạng thái duyệt qua `approvals.json` split-state. | None |
| **blueprint-to-implementation** | Compatible | Đăng ký tác vụ thực thi triển khai tới worker pool. | None |
| **implementation-to-release** | Compatible | Giải phóng các locks tài nguyên trước khi tạo commit phát hành. | None |
| **quick-feature** | Compatible | Tách biệt các tác vụ tuần tự qua DAG. | None |
| **quick-fix** | Compatible | Sử dụng luồng lập lịch tuần tự qua orchestrator. | None |
| **workflow-runtime** | Compatible | Điều khiển trung tâm dựa hoàn toàn trên Runtime API v1. | None |
| **debug-to-verify** | Compatible | Thẩm định các tiêu chuẩn ghi logs đồng bộ. | None |
| **frontend-design** | Compatible | Giám sát tài nguyên thông qua Resource Governor. | None |
| **vir-runtime** | Compatible | Tích hợp hoàn toàn các observers và sensory. | None |
| **vir-verify** | Compatible | Xác thực chéo trạng thái qua bus sự kiện. | None |
