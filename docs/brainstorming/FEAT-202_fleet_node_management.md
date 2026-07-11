<!-- docs/brainstorming/FEAT-202_fleet_node_management.md -->

---
feature_id: FEAT-202
feature_name: Fleet & Node Management
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-202_fleet_node_management_plan.md
---

# Master Requirement Document – Fleet & Node Management

## Executive Summary
Điều phối cấu hình, nâng cấp phần mềm OTA (Over-The-Air) và theo dõi tài nguyên của toàn bộ các NodeAgent.

## Vision
Khả năng tự động cài đặt và cập nhật hệ điều hành AIWF OS trên diện rộng.

## Background
Việc nâng cấp thủ công từng node rất tốn công sức và dễ xảy ra lỗi không đồng bộ phiên bản.

## Objectives
- Nâng cấp phần mềm OTA tự động.
- Cấu hình cấu hình tập trung.

## Scope
- OTA update client.
- SSH node configuration.

## Out of Scope
- Quản trị hạ tầng mạng VPN của bên thứ ba.

## Functional Requirements
- **FR-01**: Đẩy bản cập nhật phần mềm xuống Node.
- **FR-02**: Rollback phiên bản khi cập nhật lỗi.

## Non-Functional Requirements
- **NFR-01**: Băng thông tải bản cập nhật không vượt quá 5MB/s mỗi Node.

## Domain Model
`NodeAgent` có phiên bản `Version` và trạng thái `UpdateStatus`.

## Runtime Components
- `OTAUpdateEngine`
- `NodeAgent`

## Service Boundaries
NodeAgent định kỳ ping về Cloud Control Plane để lấy bản cập nhật mới.

## API Surface
- `POST /api/v1/ota/update`

## Event Model
- `ota_failed`: Phát ra khi nâng cấp Node bị lỗi.

## State Model
`IDLE` -> `DOWNLOADING` -> `UPGRADING` -> `REBOOTING`.

## Security
Tất cả các bản cập nhật OTA bắt buộc phải được ký số trước khi đẩy xuống Node.

## Scalability
Hỗ trợ cập nhật đồng thời cho 1,000 node mà không làm nghẽn băng thông server.

## High Availability
Lưu trữ bản cập nhật trên Cloudflare CDN để giảm tải máy chủ.

## Disaster Recovery
Tự động kích hoạt cơ chế khôi phục từ snapshot cũ tại local Node khi cập nhật hỏng.

## Multi-Tenancy
Mỗi tenant có danh mục phiên bản phần mềm được phê duyệt riêng.

## Cost Model
Miễn phí trong gói Control Plane cơ bản.

## Risks
- Gói cập nhật bị giả mạo. Giải pháp: Check SHA-256 signature chốt chặn.

## Trade-offs
- Thời gian cập nhật có độ trễ do mạng đổi lại việc quản lý tập trung chính xác.

## Migration Strategy
Hỗ trợ tương thích ngược với Node Agent v2.

## Acceptance Criteria
- [ ] Cập nhật thành công phiên bản phần mềm trên worker node.
