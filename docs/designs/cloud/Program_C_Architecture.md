# Program C Architecture – Security & Governance

## 1. Vision & Responsibilities
Cung cấp thư mục định danh SSO tập trung và quản lý chính sách bảo mật Node Agent.

## 2. Scope & Out of Scope
- **Scope**: OAuth2 OpenID Connect IAM, policy updates, RBAC schema.
- **Out of Scope**: Local user account database.

## 3. Topologies & Services
- **Service Topology**: OAuth2Server, PolicyEnforcer, RBACManager.
- **Deployment Topology**: High-security isolated VPC zones.

## 4. Interface & APIs
- `POST /api/v1/auth/verify`
