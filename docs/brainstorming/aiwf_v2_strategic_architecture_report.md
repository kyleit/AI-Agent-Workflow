<!-- docs/brainstorming/aiwf_v2_strategic_architecture_report.md -->

# AIWF OS v2 Strategic Architecture & Platform Evolution Report

Báo cáo này thiết lập tầm nhìn chiến lược dài hạn (North Star Architecture) và lộ trình phát triển của hệ điều hành AIWF OS trong 5–10 năm tới.

---

## 1. Product Strategy Review
AIWF OS không chỉ là một coding agent đơn lẻ, nó là một **AI Operating System Platform** - nền tảng quản trị và ảo hóa toàn bộ quy trình phát triển phần mềm được vận hành bởi AI.
- **Đối tượng người dùng**: Lập trình viên cá nhân, đội ngũ kỹ thuật doanh nghiệp (Team/Enterprise), và các AI Agent tự trị cần một môi trường ảo hóa thực thi an toàn.
- **Năng lực cốt lõi (Core Capabilities)**:
  - Máy trạng thái thực thi có khả năng tự phục hồi (Self-Healing Loop).
  - Phân vùng workspace an toàn và ảo hóa I/O (VFS Overlay).
  - Hệ sinh thái nạp nóng plugin/kỹ năng chéo môi trường (MCP Native).

---

## 2. Domain-Driven Architecture Review
AIWF OS được phân rã thành các Domain chiến lược cao nhất sau:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              AIWF OS                                   │
└────────────────────────────────────────────────────────────────────────┘
     │               │               │               │               │
┌────▼────┐     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
│ Runtime │     │ Knowledge│    │Security │     │Ecosystem│    │Operations
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
```

- **Runtime (Execution Layer)**: Quản lý scheduler, tiến trình ảo hóa và máy trạng thái.
- **Knowledge (Semantic Layer)**: Đồ thị tri thức chéo dự án và bộ nhớ tiến hóa.
- **Security (Gatekeeper Layer)**: Cô lập hộp cát ảo (WASM/MicroVM) và tường lửa câu lệnh.
- **Ecosystem (Extension Layer)**: Đăng ký đa tác nhân SDK, MCP và Marketplace.
- **Operations (Control Plane)**: Quản lý cụm node từ xa gRPC, điều phối và đo lường telemetry.

---

## 3. Capability Map (Sơ đồ năng lực)

- **Level 1: Security Domain**
  - **Level 2: Execution Isolation**
    - *Level 3 Services*: Docker Container Provider, Firecracker MicroVM, WASM Sandboxing.
    - *FEAT Mapping*: FEAT-094, FEAT-113.
- **Level 2: Access Control**
  - *Level 3 Services*: Policy Enforcement Engine, Cryptographic Signing.
  - *FEAT Mapping*: FEAT-091, FEAT-104.

- **Level 1: Runtime Domain**
  - **Level 2: Execution Coordination**
    - *Level 3 Services*: Kahn's DAG Scheduler, Loop Controller.
    - *FEAT Mapping*: FEAT-086, FEAT-087.

---

## 4. Product Evolution Roadmap (Lộ trình tiến hóa)

### AIWF Personal Edition (Cá nhân)
- **Mục tiêu**: Tối ưu tốc độ lập trình cục bộ cho nhà phát triển đơn lẻ.
- **Thành phần**: Local SQLite, VFS memory overlay, Local Docker sandbox, CLI.

### AIWF Team & Enterprise Edition (Doanh nghiệp)
- **Mục tiêu**: Phục vụ cộng tác nhóm lớn và bảo mật dữ liệu doanh nghiệp chéo máy.
- **Thành phần**: gRPC Federation Node Master, Shared Lock Engine, RBAC Policy, Remote MicroVM cluster.

### AIWF Cloud SaaS (Nền tảng dịch vụ)
- **Mục tiêu**: Cung cấp môi trường Cloud IDE tự trị chạy trên serverless pools.
- **Thành phần**: Fleet Management, Auto Scaling pools, K8s execution engine.

---

## 5. Competitive Strategy vs. Global Tech

- **Mô hình học hỏi**:
  - Học hỏi **Claude Code / Devin**: Cách tích hợp terminal monitor tương tác sâu và hiển thị logs trực quan.
  - Học hỏi **Cursor / Continue**: Chuẩn giao tiếp Model Context Protocol (MCP) rộng mở.
- **Điểm AIWF KHÔNG nên theo đuổi**:
  - Không xây dựng các mô hình LLM độc quyền lớn (giữ vị thế trung lập định tuyến model để giảm chi phí tối đa).
- **Lợi thế độc quyền**:
  - Nhân máy trạng thái loop độc lập có khả năng rollback 3 lớp (Code, DB, State) khi gặp lỗi biên dịch.

---

## 6. AIWF North Star Architecture (Kiến trúc 5 năm tới)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                               │
├────────────────────────────────────────────────────────────────────────┤
│     Knowledge Layer (Graph DB)     │    Intelligence Layer (Router)    │
├────────────────────────────────────────────────────────────────────────┤
│                     Multi-Agent Collaboration SDK                      │
├────────────────────────────────────────────────────────────────────────┤
│           Runtime Kernel & MicroVM Hardware Virtualization             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Final Scope Review (Định vị phạm vi v2)
Để đảm bảo v2 thực thi khả thi và hướng tới North Star, phạm vi v2 được tinh chỉnh như sau:
- **Core v2 (Duy trì)**: FEAT-109 (Distributed), FEAT-110 (Cognitive), FEAT-111 (Collaboration), FEAT-112 (MCP Engine), FEAT-113 (MicroVM Sandbox).
- **Chuyển dịch sang v3**: Fleet Management chéo cloud, Distributed Consensus chéo cluster (chuyển từ v2 Core sang v3).
- **Chuyển dịch sang Enterprise/SaaS**: Cấu hình Billing & API Token Gateway chéo cụm.
- **Chuyển thành Plugin (Marketplace)**: Các bộ adapter chuyển đổi legacy IDEs của bên thứ ba.
