<!-- docs/brainstorming/FEAT-205_cloud_api_gateway.md -->

---
feature_id: FEAT-205
feature_name: Cloud API Gateway
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-205_cloud_api_gateway_plan.md
---

# Master Requirement Document – Cloud API Gateway

## Executive Summary
Cổng kết nối API Gateway quản trị traffic, giới hạn rate limit và mã hóa kết nối giữa Cloud và các Node cục bộ.

## Vision
Cổng API hiệu suất cao chịu tải hàng triệu kết nối thời gian thực.

## Background
Thiếu lớp Gateway dẫn đến việc khó bảo vệ các Node khi mở cổng trực tiếp ra internet.

## Objectives
- Rate limiting và bảo vệ DDoS.
- Routing request gRPC/WebSockets.

## Scope
- API Gateway Proxy.
- Rate Limiter Module.

## Out of Scope
- Biên dịch logic mã nguồn của backend.

## Functional Requirements
- **FR-01**: Định tuyến request tới đúng Node Agent.
- **FR-02**: Giới hạn số kết nối từ một IP trong một phút.

## Non-Functional Requirements
- **NFR-01**: Trễ định tuyến gateway nhỏ hơn 2ms.

## Domain Model
`Route` ánh xạ `RequestPath` tới `TargetService`.

## Runtime Components
- `APIGatewayProxy`
- `RateLimiter`

## Service Boundaries
Nằm ở lớp ngoài cùng của cụm cloud để tiếp nhận toàn bộ traffic đầu vào.

## API Surface
- `ANY /api/*`

## Event Model
- `rate_limit_exceeded`: Bắn ra khi vượt ngưỡng rate limit.

## State Model
`HEALTHY` -> `CONGESTED`.

## Security
Tích hợp SSL Offloading, Web Application Firewall (WAF) và chặn IP độc hại.

## Scalability
Hỗ trợ 500,000 RPS (Requests Per Second).

## High Availability
Triển khai thông qua AWS NLB (Network Load Balancer) chéo các vùng.

## Disaster Recovery
Sử dụng DNS Failover (Cloudflare) định tuyến sang backup gateway nếu cụm chính chết.

## Multi-Tenancy
Mỗi tenant được gán quota request/giây riêng.

## Cost Model
Tính phí theo dung lượng băng thông dữ liệu đi qua gateway.

## Risks
- Sập Gateway làm gián đoạn toàn bộ hệ thống. Giải pháp: Chạy cụm Gateway tối thiểu 3 node active.

## Trade-offs
- Thêm một bước trung chuyển mạng làm tăng nhẹ latency nhưng đảm bảo an ninh.

## Migration Strategy
Hoàn toàn tương thích ngược với API REST/WebSockets của v2.

## Acceptance Criteria
- [ ] Gateway định tuyến request thành công và chặn IP spam.
