# AIWF Platform Benchmark Specification

Đặc tả đo lường chất lượng và hiệu năng của Runtime.

## 1. Các tiêu chuẩn đo lường (Metrics)
- **Thời gian khởi động (Startup Latency)**: Yêu cầu < 0.8 giây cho CLI.
- **Thời gian tự chữa lành (Recovery Latency)**: Yêu cầu < 2.0 giây sau khi tiến trình daemon bị sập đột ngột.
- **Mức tải CPU (CPU Overhead)**: Watchdog Supervisor sử dụng < 1% CPU máy trạm.
