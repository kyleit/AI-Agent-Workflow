<!-- File path: docs/program-governance/cloud/Cloud_Program_Governance.md -->

# AIWF Cloud Program Governance Report

Tài liệu này định nghĩa khung quản trị và chất lượng cho các chương trình (Programs) thuộc AIWF Cloud.

---

## 1. Cloud Program Governance Principles
- **PG-C01 Interface First**: Mọi micro-service của Cloud chỉ được giao tiếp qua REST/gRPC API được định nghĩa sẵn.
- **PG-C02 Strict Isolation**: Cô lập dữ liệu multi-tenancy chéo cơ sở dữ liệu logical.
- **PG-C03 Auditability**: Lưu logs truy vết cho 100% các thao tác thay đổi quyền hạn.

---

## 2. Capability Catalog & Ownership Model
- **Cap-C01: Distributed Resource Scheduling**
  - *Owner*: Program B (Distributed Scheduling).
  - *Layer*: Platform Service Layer.
  - *Business Value*: Tối ưu 50% chi phí phần cứng vật lý chéo node.
- **Cap-C02: Multi-tenant SSO authentication**
  - *Owner*: Program C (Security & Governance).

---

## 3. Program & Initiative Contracts
Các micro-services của Cloud giao tiếp với NodeAgent dưới local thông qua mTLS gRPC:
- **Heartbeat Contract**: NodeAgent phải báo cáo trạng thái mỗi 5 giây.
- **OTA Distribution Contract**: Bản build phần mềm được phân phối dạng signed zip.

---

## 4. Responsibility & Dependency Matrix
- **AIWF OS**: Quản lý Local VFS, Process Table, SQLite WAL local storage.
- **AIWF Cloud**: Quản lý Global Route, SSO Directory, Private/Public plugin Marketplace registry, Regional DR replication.
- **gRPC / mTLS APIs**: Ranh giới cứng duy nhất giữa Cloud và OS kernel. Không chia sẻ trực tiếp file system.
