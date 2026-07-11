<!-- File path: docs/plans/cloud/Cloud_Master_Roadmap.md -->

# AIWF Cloud Master Roadmap & Program Planning Report

Tài liệu này chi tiết hóa kế hoạch lập lịch chương trình (Program Planning) chéo toàn bộ các Domain và sáng kiến của AIWF Cloud (FEAT-201 đến FEAT-210).

---

## 1. Program Plans (Kế hoạch Chương trình)
- **Program A: Cloud Operations (FEAT-202, FEAT-206)**
  - *Vision*: Giám sát và nâng cấp tự động hàng vạn NodeAgent an toàn.
  - *Objectives*: OTA updates, logs ClickHouse centralization.
  - *Success Metrics*: 100% NodeAgent được cập nhật đồng nhất dưới 10 phút.
  - *Dependencies*: Phụ thuộc vào VFS và Event Journal SQLite của v2.
  
- **Program B: Distributed Scheduling (FEAT-203)**
  - *Vision*: Định tuyến tác vụ nhận thức tối ưu chi phí chéo node.
  - *Objectives*: Multi-cluster gRPC scheduler.
  
- **Program C: Security & Governance (FEAT-204, FEAT-207)**
  - *Vision*: Chốt chặn IAM doanh nghiệp và đồng bộ hóa Policy từ Cloud.
  
- **Program D: Cloud Interface & Gateway (FEAT-201, FEAT-205)**
  - *Vision*: Cổng Gateway chịu tải cao và giao diện Web dashboard.
  
- **Program E: Ecosystem & DR (FEAT-208, FEAT-209, FEAT-210)**
  - *Vision*: Private/public marketplace, S3 artifact sharing và multi-region DR.

---

## 2. Initiative Plans (Kế hoạch Sáng kiến)
- **Initiative A1: OTA update (Program A)**
  - *Deliverables*: Client OTA, sign verification module.
  - *ADR Count*: 3. *Blueprint Count*: 2. *Sprint Count*: 1.
- **Initiative B1: Distributed Scheduler (Program B)**
  - *Deliverables*: gRPC dispatch router, cluster balance estimator.
  - *ADR Count*: 4. *Blueprint Count*: 2. *Sprint Count*: 2.

---

## 3. Feature Plans Mapping (Phân rã FEAT-201 đến FEAT-210)
- **FEAT-201 (Cloud Control Plane)**: Initiative D1. REST APIs & Dashboard interface. Dod: Web UI displays registered nodes.
- **FEAT-202 (Fleet Management)**: Initiative A1. OTA updates client.
- **FEAT-203 (Distributed Scheduler)**: Initiative B1. Resource-aware task distributor.
- **FEAT-204 (RBAC & Org)**: Initiative C1. SSO directory authentication.
- **FEAT-205 (API Gateway)**: Initiative D2. WAF and proxy routing logic.
- **FEAT-206 (Observability Platform)**: Initiative A2. ClickHouse log ingester.
- **FEAT-207 (Cloud Policy)**: Initiative C2. Encrypted policy updates client.
- **FEAT-208 (Artifact Distribution)**: Initiative E1. S3 bucket sync helper.
- **FEAT-209 (Marketplace)**: Initiative E2. MCP tool validation server.
- **FEAT-210 (Multi-Region DR)**: Initiative E3. Regional database replica sync.

---

## 4. Cross-Program Planning & Dependency Graph
```text
[Program D: Gateway] ──> [Program C: IAM & Policy] ──> [Program B: Scheduler] ──> [Program A: Operations]
                                                            │
                                                        [Program E: DR]
```
- **Đường găng (Critical Path)**: Program D (Gateway) -> Program C (IAM) -> Program B (Scheduler).
- **Phân bổ tài nguyên**: Đội ngũ phát triển chia thành 3 nhóm chạy song song các Program độc lập.
- **Ma trận rủi ro**: Rủi ro mất đồng bộ DB chéo vùng (FEAT-210). Giảm thiểu bằng cơ chế đồng thuận Quorum.
