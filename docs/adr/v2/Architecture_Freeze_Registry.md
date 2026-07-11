# AIWF v2 Architecture Freeze Registry

Danh mục phân loại mức độ ổn định và các nguyên tắc biên giới kiến trúc của AIWF v2.

---

## 1. ADR Stability Matrix
| ADR ID | Tên quyết định | Phân loại (Frozen / Stable / Experimental) |
| :--- | :--- | :---: |
| ADR-047 | gRPC Distributed Runtime | **Frozen** (Public APIs và Protocol đóng băng) |
| ADR-048 | Context Routing & Healing | **Stable** (Thiết kế chốt, thuật toán tinh chỉnh sau) |
| ADR-049 | SQLite Distributed Locks | **Frozen** (Lock model SQLite đóng băng) |
| ADR-050 | ZIP Plugin Signature & MCP | **Stable** (Giao thức ZIP chốt, MCP có thể mở rộng) |
| ADR-051 | Firecracker microVM Sandbox | **Experimental** (Có thể thay đổi cơ chế boot kernel) |
| ADR-052 | Shared Message Envelope | **Frozen** (Cấu trúc envelope đóng băng) |

---

## 2. Quy trình đề xuất thay đổi (Architecture Change Proposal - ACP)
1. Chỉ các ADR thuộc nhóm **Experimental** hoặc **Stable** mới được đề xuất ACP.
2. Mọi thay đổi cấu hình đối với ADR nhóm **Frozen** phải có sự phê duyệt trực tiếp của Chief System Architect.

---

## 3. Biên giới Kiến trúc Blueprint (Blueprint Boundaries)
- Blueprint của Program A tuyệt đối không được tự ý sinh mã nguồn xử lý token của Program B.
- Blueprint của Program D (Plugin) phải sử dụng hoàn toàn VFS ảo của Program C để ghi tệp tin lên host OS.
