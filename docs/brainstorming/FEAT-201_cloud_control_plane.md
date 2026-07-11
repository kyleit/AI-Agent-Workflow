<!-- docs/brainstorming/FEAT-201_cloud_control_plane.md -->

---
feature_id: FEAT-201
feature_name: Cloud Control Plane
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-201_cloud_control_plane_plan.md
---

# Master Requirement Document – Cloud Control Plane

## Executive Summary
AIWF Cloud Control Plane cung cấp giao diện quản trị trung tâm để cấu hình và theo dõi hàng nghìn cụm máy chạy AIWF OS.

## Vision
Trở thành bảng điều khiển (Control Center) quản trị fleet AI mạnh mẽ, kết nối liền mạch với các agent từ xa.

## Background
AIWF OS hoạt động phân tán đơn lẻ và thiếu khả năng điều phối tập trung trên quy mô doanh nghiệp.

## Objectives
- API Gateway điều phối tập trung.
- Dashboard giao diện web quản trị.

## Scope
- Quản lý trạng thái fleet.
- Cấu hình cluster tập trung.

## Out of Scope
- Tự động thay thế phần cứng vật lý.

## Functional Requirements
- **FR-01**: Cập nhật trạng thái Node theo thời gian thực.
- **FR-02**: Quản lý tài khoản doanh nghiệp.

## Non-Functional Requirements
- **NFR-01**: Thời gian tải dashboard dưới 1 giây.

## Domain Model
`Organization` sở hữu nhiều `Workspaces` và các `Nodes`.

## Runtime Components
- `CloudControlPlaneService`

## Service Boundaries
Sử dụng RESTful và gRPC API giao tiếp trực tiếp với AIWF OS kernel.

## API Surface
- `GET /api/v1/nodes`

## Event Model
- `node_registered`: Bắn ra khi có node agent đăng ký mới.

## State Model
`STANDBY` -> `ACTIVE` -> `FAILING`.

## Security
Xác thực tài khoản qua OAuth2 / OpenID Connect.

## Scalability
Hỗ trợ quản trị tới 10,000 nodes đồng thời.

## High Availability
Chạy multi-replica trên Kubernetes chéo AWS AZs.

## Disaster Recovery
Backup database định kỳ sang AWS S3.

## Multi-Tenancy
Mỗi Organization được cô lập logic ở tầng database schema.

## Cost Model
Tính phí theo số lượng Nodes hoạt động (Pay-as-you-go).

## Risks
- Rò rỉ thông tin cấu hình nhạy cảm. Giải pháp: Mã hóa mọi tệp tin lưu trữ.

## Trade-offs
- Tăng độ phức tạp quản trị cluster đổi lại tính nhất quán của fleet node.

## Migration Strategy
Cung cấp API import các file cấu hình `workflow.json` cũ từ v2.

## Acceptance Criteria
- [ ] Hiển thị danh sách node trên dashboard chính xác.
