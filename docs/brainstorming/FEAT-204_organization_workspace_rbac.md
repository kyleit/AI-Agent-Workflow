<!-- docs/brainstorming/FEAT-204_organization_workspace_rbac.md -->

---
feature_id: FEAT-204
feature_name: Organization, Workspace & RBAC
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-204_organization_workspace_rbac_plan.md
---

# Master Requirement Document – Organization, Workspace & RBAC

## Executive Summary
Quản trị tổ chức (Organizations), không gian làm việc nhóm (Workspaces) và phân quyền chi tiết RBAC cho người dùng và Agent.

## Vision
Cung cấp giải pháp bảo mật phân quyền đa tầng cho các nhóm lập trình lớn.

## Background
AIWF v2 chỉ hỗ trợ phân quyền cục bộ flat cấu hình qua JSON tĩnh của Policy Engine.

## Objectives
- Quản lý phân quyền RBAC qua Web UI.
- Đồng bộ Identity chéo hệ thống.

## Scope
- RBAC Engine.
- User/Agent Directory.

## Out of Scope
- Quản lý thanh toán lương nhân viên.

## Functional Requirements
- **FR-01**: Tạo Organization và thêm thành viên.
- **FR-02**: Phân quyền Read/Write tệp tin cho Agent.

## Non-Functional Requirements
- **NFR-01**: Thời gian phản hồi phân quyền xác thực dưới 5ms.

## Domain Model
`User` có nhiều `Roles` gán các `Permissions` trong `Workspace`.

## Runtime Components
- `IdentityManager`
- `RBACAuthorizer`

## Service Boundaries
Tương tác trực tiếp với API Gateway để xác thực yêu cầu.

## API Surface
- `POST /api/v1/auth/check`

## Event Model
- `role_assigned`: Phát ra khi gán quyền mới cho thành viên.

## State Model
`ACTIVE` -> `SUSPENDED`.

## Security
Mã hóa JWT token và hỗ trợ bảo mật SSO (Single Sign-On).

## Scalability
Hỗ trợ tối đa 1 triệu người dùng/agents.

## High Availability
Sử dụng Redis cache để lưu trữ quyền hạn của session ID.

## Disaster Recovery
Tự động đồng bộ quyền hạn từ database chính sang replica.

## Multi-Tenancy
Mỗi tenant có một tenant_id cô lập tuyệt đối ở tầng logic SQL.

## Cost Model
Tính phí theo số lượng người dùng hoạt động hàng tháng (MAU).

## Risks
- Leo thang đặc quyền (Privilege Escalation). Giải pháp: Audit logs tự động cho mọi hành vi gán quyền.

## Trade-offs
- Thời gian trễ nhẹ khi check quyền đổi lại bảo mật an toàn cấp doanh nghiệp.

## Migration Strategy
Import cấu hình Policy Engine cũ lên Cloud RBAC.

## Acceptance Criteria
- [ ] Chặn thành công Agent truy cập tệp khi không có quyền ghi.
