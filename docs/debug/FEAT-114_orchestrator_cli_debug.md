# Debug Log — FEAT-114: Resident Orchestrator CLI

Báo cáo phân tích và chẩn đoán sự cố trong quá trình phát triển nhóm lệnh `orchestrator` CLI.

## 1. Nhật ký chẩn đoán lỗi
Trong quá trình chạy kiểm thử đơn vị (`test_orchestrator_cli.py`), hệ thống báo lỗi không tìm thấy tác nhân hoạt động tại `test_agents_workflows_queue_graph_locks`. 

- **Nguyên nhân**: Hàm `resolve_state_dir` mặc định phân giải thư mục trạng thái theo `work_item_id` nếu có (mặc định là `"FEAT-111"`), dẫn đến tìm kiếm các tệp `agents.json`, `task_graph.json` dưới thư mục scoped `work-items/FEAT-111/orchestrator` thay vì thư mục toàn cục `orchestrator`.
- **Khắc phục**: Cập nhật ca kiểm thử để ghi các tệp giả lập trực tiếp vào thư mục scoped tương ứng với mã công việc hoạt động.

## 2. Các sự cố đã khắc phục
- Lỗi định tuyến thư mục trạng thái đã được giải quyết hoàn toàn, đảm bảo mọi ca kiểm thử đơn vị đều đi qua thành công.
