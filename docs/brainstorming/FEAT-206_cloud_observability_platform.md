<!-- docs/brainstorming/FEAT-206_cloud_observability_platform.md -->

---
feature_id: FEAT-206
feature_name: Cloud Observability Platform
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-206_cloud_observability_platform_plan.md
---

# Master Requirement Document – Cloud Observability Platform

## Executive Summary
Nền tảng giám sát tập trung lưu trữ log, trace sự kiện chéo node và báo cáo chi phí token tự động của AIWF.

## Vision
Hệ thống giám sát E2E phân tán cung cấp bức tranh chi tiết về hoạt động lập trình tự động của AI.

## Background
Logs của v2 lưu cục bộ tại SQLite của từng Node và không có góc nhìn tổng thể cho doanh nghiệp.

## Objectives
- Tập trung hóa Logs/Metrics/Traces.
- Biểu đồ phân tích chi phí token thời gian thực.

## Scope
- Log Collector Agent.
- Centralized Tracing Engine.

## Out of Scope
- Giám sát các thiết bị IoT ngoài luồng phát triển.

## Functional Requirements
- **FR-01**: Thu thập logs của NodeAgent về Cloud.
- **FR-02**: Vẽ sơ đồ phân tích thời gian chạy từng Task.

## Non-Functional Requirements
- **NFR-01**: Trễ đồng bộ log từ Node về Cloud dưới 2 giây.

## Domain Model
`LogEntry` và `TraceSpan` được liên kết bởi `CorrelationID`.

## Runtime Components
- `LogCollector`
- `MetricsExporter`

## Service Boundaries
Đọc dữ liệu từ SQLite Event Journal cục bộ của Node và đẩy về Cloud.

## API Surface
- `POST /api/v1/telemetry/ingest`

## Event Model
- `alert_triggered`: Phát đi khi hệ thống phát hiện chỉ số CPU/RAM vượt ngưỡng.

## State Model
`COLLECTING` -> `BUFFERING` -> `INGESTED`.

## Security
Mã hóa dữ liệu log lúc truyền tải và che giấu (masking) các thông tin nhạy cảm.

## Scalability
Xử lý lưu trữ tới 10TB logs mỗi ngày.

## High Availability
Lưu trữ log trên cụm Elasticsearch hoặc ClickHouse phân tán.

## Disaster Recovery
Lưu trữ cold backup dữ liệu logs trên AWS Glacier.

## Multi-Tenancy
Cô lập tuyệt đối không gian log theo từng ID tổ chức.

## Cost Model
Tính phí theo dung lượng lưu trữ GB/tháng.

## Risks
- Dung lượng logs quá lớn làm tràn bộ nhớ máy chủ. Giải pháp: Đặt chính sách xóa logs sau 30 ngày (retention policy).

## Trade-offs
- Chi phí hạ tầng lưu trữ ClickHouse tương đối cao.

## Migration Strategy
Hỗ trợ nạp logs cấu trúc SQLite Event Journal của v2 lên Cloud.

## Acceptance Criteria
- [ ] Log đẩy lên được tìm thấy trên Cloud interface chính xác.
