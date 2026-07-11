<!-- File path: docs/brainstorming/aiwf_cloud_strategic_report.md -->

# AIWF Cloud Strategic Architecture & Competitive Report

Báo cáo này làm rõ ranh giới kiến trúc, danh mục dịch vụ và chiến lược cạnh tranh toàn cầu của AIWF Cloud.

---

## 1. Cloud vs. AIWF OS Responsibility Matrix
| Thành phần / Trách nhiệm | AIWF OS (Kernel cục bộ) | AIWF Cloud (Control Plane) |
| :--- | :---: | :---: |
| Thực thi Task Graph cục bộ | **Sở hữu** | Không |
| Quản lý VFS / Cache địa phương | **Sở hữu** | Không |
| Điều phối đa cụm Node chéo mạng | Không | **Sở hữu** |
| Đăng ký Phân quyền Tổ chức RBAC | Không | **Sở hữu** |
| OTA update / Fleet Monitoring | Không | **Sở hữu** |
| Chợ ứng dụng công cộng Marketplace | Client nạp | **Lưu trữ & Xác thực** |

---

## 2. Cloud Service Catalog & Domain Map
- **Fleet Management Service**: Quản trị danh sách Node và cấu hình OTA.
- **Distributed Scheduler Service**: Định tuyến và lập lịch phân phối tác vụ thông minh.
- **Identity & RBAC Service**: Quản lý tài khoản doanh nghiệp SSO và quyền truy cập workspace.
- **Observability Hub**: ClickHouse-based collector gom logs/telemetry chéo node.

---

## 3. Competitive Comparison Against Global Orchestrators
- **vs. Kubernetes**: Kubernetes quản lý container chung; AIWF Cloud quản lý luồng nhận thức (Cognitive task workflow) và trạng thái bộ nhớ chéo node của các Coder/Reviewer agents.
- **vs. Temporal**: Temporal là một orchestrator dạng code chung chung; AIWF Cloud được thiết kế đặc thù tối ưu hóa chi phí token, model fallback và tự sửa lỗi self-healing của AI OS.

---

## 4. Capability Mapping Recommendation
- **AIWF OS**: Local VFS, Rollback, Process Manager, SQLite Journal.
- **AIWF Cloud**: gRPC Scheduler, Centralized telemetry, SSO/RBAC directory, Cloud Marketplace registry.
