# Real Project Validation Debug Report — FEAT-111/112/113 Runtime

Báo cáo phân tích chẩn đoán lỗi trong quá trình chạy thử nghiệm thực tế.

## 1. Thread Pool Concurrency Limits
- *Phát hiện*: Khi chạy parallel các Subagents giả lập trên Windows, thread pool đôi khi gặp hiện tượng block luồng cha nếu I/O ghi đĩa không đồng bộ.
- *Khắc phục*: Tách biệt hoàn toàn luồng I/O của watchdog và luồng I/O của scheduler bằng hai executor độc lập.

## 2. Lock File Contention
- *Phát hiện*: Tranh chấp ghi file `locks.json` giữa các subagents xảy ra khi trạng thái chuyển nhanh.
- *Khắc phục*: Tăng số lần thử lại ghi tệp nguyên tử (atomic retry counter) lên 10 lần với độ trễ tăng dần.
