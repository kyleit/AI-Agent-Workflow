# ADR-056: API Gateway and Centralized IAM Policy

- **Status**: Proposed
- **Program**: Program C
- **Domain**: Security & Gateway
- **Related FEATs**: FEAT-204, FEAT-205, FEAT-207
- **Context & Problem**: Cần bảo vệ an toàn cho các Node Agent và phân quyền người dùng SSO doanh nghiệp.
- **Decision**: Sử dụng Kong/NGINX làm API Gateway; xác thực tập trung OAuth2/OIDC và đồng bộ Policy rule dạng signed JSON.
- **Consequences**: Bảo vệ DDoS hiệu quả chốt chặn ngoài rìa.
- **Backward Compatibility**: Node Agent v2 sử dụng policy token cục bộ tương thích hoàn toàn.
