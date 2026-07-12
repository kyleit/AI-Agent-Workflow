# Thiết kế tối ưu hóa chạy kiểm thử (Test Execution Optimization) cho AIWF

Tài liệu này đặc tả thiết kế kỹ thuật chi tiết của hệ thống điều phối kiểm thử tập trung (Test Coordinator) nhằm giảm thiểu tài nguyên tiêu thụ, chống chạy trùng lặp tiến trình và tối ưu hóa việc thông tin tiến trình trong AIWF.

## 1. Vấn đề hiện tại
- Mỗi Agent hoặc phiên làm việc khác nhau khi có yêu cầu kiểm thử sẽ tự động chạy một tiến trình `pytest` độc lập. Điều này gây xung đột và cạn kiệt CPU/RAM (lỗi OOM).
- Lượng log tiến độ được ghi ra màn hình quá nhiều gây nhiễu và làm chậm quá trình hiển thị.
- Không có cách theo dõi tập trung hàng đợi và trạng thái các tiến trình kiểm thử đang chạy.

## 2. Giải pháp kỹ thuật

### 2.1 Bộ điều phối kiểm thử (Test Coordinator)
- Module: [test_coordinator.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/test_coordinator.py)
- Quản lý trạng thái thông qua tệp tin JSON tập trung: `.agents/state/test-coordinator.json`.
- Sử dụng cơ chế khóa tệp chéo tiến trình (`pytest_coordinator.lock`) thông qua lớp `OSFileLock` để đảm bảo tính toàn vẹn dữ liệu khi đọc ghi trạng thái.

### 2.2 Thuật toán Chống trùng lặp (Deduplication)
- Trước khi chạy, Test Coordinator tính toán mã băm `dedup_key` dựa trên:
  `project_id:work_item_id:test_mode:test_scope:git_revision:changed_files_hash`
- Nếu phát hiện có tiến trình đang hoạt động (active run) có cùng `dedup_key`, tiến trình gọi sẽ đăng ký (subscribe) vào tiến trình đó và chờ đợi kết quả thông qua thăm dò tệp đầu ra `.agents/state/test_outcome_<dedup_key>.json`.
- Điều này loại bỏ hoàn toàn việc chạy 2 lần cùng một bộ test khi không có sự thay đổi về mã nguồn hay môi trường.

### 2.3 Quản lý Hàng đợi và Giới hạn tài nguyên (Queue & Limits)
- Giới hạn tối đa tiến trình pytest chạy song song mặc định là `1` (cấu hình qua `test_execution.max_parallel_pytest_processes`).
- Trước khi chạy pytest, Test Coordinator kiểm tra mức sử dụng CPU/RAM:
  - Nếu vượt quá ngưỡng cảnh báo/giới hạn hoặc số tiến trình song song đạt giới hạn, yêu cầu kiểm thử được đẩy vào hàng đợi (`queue`).
  - Các yêu cầu trong hàng đợi sẽ tự động thăm dò và chuyển sang trạng thái hoạt động (active) khi tiến trình trước đó hoàn thành và tài nguyên hệ thống ổn định trở lại.

### 2.4 Cập nhật Tiến độ tối giản (Sparse Progress Log)
- Phân tích luồng `stdout` thời gian thực từ `pytest` sử dụng regex để trích xuất tỷ lệ hoàn thành `%`.
- Chỉ in tiến độ ra console tại các mốc `START`, `25%`, `50%`, `75%`, `100%`, hoặc `FAIL` để tránh spam log.
- Toàn bộ log chi tiết vẫn được lưu đầy đủ trên đĩa tại `artifacts/test-runs/<run_id>/stdout.log` và `stderr.log` phục vụ việc gỡ lỗi chuyên sâu.

### 2.5 Kiểm thử độ bền bỉ (Stability Mode)
- Cung cấp tùy chọn chạy lặp 100 lần đối với các tệp tin kiểm thử bất đồng bộ/khóa tranh chấp quan trọng (`test_lock.py`, `test_concurrency.py`).
- Quá trình chạy lặp được thực thi bởi một tiến trình con chạy ngầm độc lập hoàn toàn, không chặn giao diện và ghi log chi tiết xuống đĩa.
