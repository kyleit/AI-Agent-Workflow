<!-- docs/brainstorming/FEAT-203_distributed_scheduler.md -->

---
feature_id: FEAT-203
feature_name: Distributed Scheduler
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-203_distributed_scheduler_plan.md
---

# Master Requirement Document – Distributed Scheduler

## Executive Summary
Lập lịch phân tán điều phối Task Graph chéo nhiều NodeAgent dựa trên dung lượng CPU/RAM/GPU thực tế và chi phí model.

## Vision
Hệ thống lập lịch tối ưu hóa chi phí và băng thông mạng chéo vùng địa lý (cross-region).

## Background
Lập lịch phân tán v2 chỉ chạy mức Master-Worker đơn giản trong mạng LAN cục bộ.

## Objectives
- Scheduler đa cụm (Multi-cluster scheduler).
- Định tuyến tác vụ thông minh dựa trên độ ưu tiên.

## Scope
- Global Scheduler Engine.
- Resource Estimator.

## Out of Scope
- Tự động thay đổi mã nguồn logic nghiệp vụ của task.

## Functional Requirements
- **FR-01**: Phân chia task vào node có latency thấp nhất.
- **FR-02**: Giới hạn tối đa số task chạy song song mỗi node.

## Non-Functional Requirements
- **NFR-01**: Độ trễ lập lịch dưới 100ms.

## Domain Model
`Task` thuộc `TaskGraph` được gán vào `NodeAgent`.

## Runtime Components
- `GlobalScheduler`
- `ResourceEstimator`

## Service Boundaries
Kết nối với gRPC API của các worker node agent.

## API Surface
- `POST /api/v1/schedule`

## Event Model
- `task_rescheduled`: Phát đi khi task được chuyển tiếp sang node mới.

## State Model
`QUEUED` -> `SCHEDULED` -> `DISPATCHED`.

## Security
Mã hóa mTLS cho mọi dữ liệu payload của task khi phân phối.

## Scalability
Hỗ trợ lập lịch 100,000 tasks mỗi phút.

## High Availability
Chạy active-active trên 3 Kubernetes zones.

## Disaster Recovery
Queue lưu trong PostgreSQL cluster có cơ chế Failover tự động.

## Multi-Tenancy
Mỗi tenant có hàng đợi ưu tiên cô lập độc lập.

## Cost Model
Tính phí dựa trên lượng thời gian CPU/GPU sử dụng.

## Risks
- Bị nghẽn hàng đợi (queue blocking). Giải pháp: Đặt mức trần timeout tác vụ.

## Trade-offs
- Chi phí đồng bộ trạng thái graph chéo mạng tăng lên.

## Migration Strategy
Hỗ trợ nạp cấu hình DAG Task Graph cũ của v1/v2.

## Acceptance Criteria
- [ ] Phân bổ task đúng node có tài nguyên trống.
