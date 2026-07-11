<!-- File path: docs/brainstorming/aiwf_cloud_strategic_architecture_report.md -->

# AIWF Cloud Strategic Architecture Review Report

Báo cáo này thẩm định thiết kế chiến lược dài hạn và định vị ranh giới của AIWF Cloud trong hệ sinh thái AIWF OS.

---

## 1. Product Strategy & Competitive Analysis
AIWF Cloud định vị là **Distributed Multi-Agent Control Plane** chịu trách nhiệm điều phối hàng vạn worker chạy AIWF OS.
- **Phân tích cạnh tranh**:
  - **vs. Temporal / Argo**: Temporal không có khái niệm về Agent, bộ nhớ chéo node (shared memory context) hay tối ưu hóa mô hình LLM. AIWF Cloud lấp đầy khoảng trống này bằng cách cung cấp Distributed Scheduler định hướng AI.
  - **vs. Kubernetes**: Kubernetes quản lý vòng đời Container; AIWF Cloud quản lý vòng đời nhận thức (Cognitive lifecycles) và sự đồng thuận chéo tác nhân (Consensus).

---

## 2. Cloud Capability Catalog & Domain Map
- **Domain: Fleet Operations**
  - **Capability**: OTA updates, node health telemetry.
  - **Service**: FleetManager, LogCollector.
  - **FEATs**: FEAT-202, FEAT-206.
- **Domain: Security & IAM**
  - **Capability**: SSO Organization directory, RBAC checks.
  - **Service**: OAuth2 IAM, PolicyEngine.
  - **FEATs**: FEAT-204, FEAT-207.

---

## 3. Responsibility Matrix
- **AIWF OS (Kernel)**: Chạy cục bộ Task Graph, VFS, Process Manager.
- **AIWF Cloud**: gRPC Scheduler, Multi-region DR, IAM Directory, private/public Marketplace registry.
- **AIWF SDK**: Các hook, wrapper cho phép phát triển plugin của bên thứ ba.

---

## 4. North Star Cloud Architecture
```text
┌────────────────────────────────────────────────────────────────────────┐
│                        API Gateway / WAF Portal                        │
├────────────────────────────────────────────────────────────────────────┤
│  Federation Scheduler (AP/US)  │     SSO / RBAC IAM Org Directory      │
├────────────────────────────────────────────────────────────────────────┤
│           Fleet Management & OTA Update Distribution Registry          │
├────────────────────────────────────────────────────────────────────────┤
│               Distributed ClickHouse Telemetry Database                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Scope Freeze Proposal
- **Đóng băng v2 Cloud**: Hoàn thành toàn bộ FEAT-201 đến FEAT-210 ở dạng micro-services độc lập, chạy trên Kubernetes AWS EKS.
- Không tích hợp trực tiếp các driver phần cứng ảo vào Cloud Control Plane (để driver dưới nhân OS).
