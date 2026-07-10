<!-- File path: docs/quick/QUICK-026_global_obsidian_vault_root_provisioning.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-026
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Add Global Obsidian Vault Root and Per-Project Folder Auto-Provisioning

| 🔒 QUICK-FEATURE MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the QUICK feature specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/quick/QUICK-026_global_obsidian_vault_root_provisioning.md` |
| Design Blueprint path: `docs/designs/QUICK-026_global_obsidian_vault_root_provisioning_blueprint.md` |

---

## 1. Feature Goal
Nâng cấp Machine-Level Global Provider Manager và Knowledge Runtime để hỗ trợ cấu hình Obsidian một lần với một thư mục root dùng chung (`vault_root`), từ đó mỗi dự án AIWF chạy trên máy tính sẽ tự động được cấp phát và đồng bộ vào thư mục Obsidian con riêng biệt (`vault_root/AIWF-Knowledge-{project_slug}/`).

## 2. Scope

### In Scope
- **Mở rộng Cấu hình Toàn cục**:
  - Hỗ trợ các thuộc tính mới của Obsidian: `vault_root`, `project_folder_pattern`, `create_if_missing`, `sync_structure`.
  - Tương thích ngược: Nếu có `vault_path` mà không có `vault_root`, coi `vault_path` là `vault_root` và đưa ra cảnh báo di chuyển cấu hình.
- **Project Folder Resolution**:
  - Cung cấp hàm `resolve_obsidian_project_folder(project_root=".") -> str`.
  - Nhận diện ID dự án (thứ tự ưu tiên: `.agents/memory.config.json` -> `project_id`, `.agents/project-profile.json` -> project name/id, Git repository root folder, Workspace folder).
  - Chuẩn hóa tên dự án thành `project_slug` ổn định (chữ thường, thay khoảng trắng thành `-`, lọc ký tự không an toàn, gộp ký tự phân tách liên tiếp, cắt bỏ ký tự phân tách ở đầu/cuối).
  - Tự động tạo thư mục con và tệp `README.md` mô tả dự án (với các thông tin bảo mật đã ẩn).
- **Lưu trữ Ánh xạ Dự án**:
  - Lưu và đọc thông tin ánh xạ tại `.agents/knowledge/obsidian-project-map.json`.
  - Nếu đã có ánh xạ từ trước, tái sử dụng `vault_folder` cũ ngay cả khi dự án đổi tên.
  - Nếu đổi `vault_root`, cập nhật lại `resolved_path` nhưng giữ nguyên cấu trúc `vault_folder`.
  - Kiểm tra và ngăn chặn xung đột nếu thư mục đã thuộc về dự án khác.
- **Đồng bộ Thư mục & Chế độ Sync**:
  - Định nghĩa bản đồ ánh xạ thư mục AIWF sang Obsidian (ví dụ: `docs/brainstorming/` -> `Brainstorming/`) thông qua cấu hình `folder_mapping` ở global hoặc mặc định.
  - Hỗ trợ 4 chế độ: `file-sync` (mặc định), `readonly`, `rest`, `bidirectional`.
  - Thiết lập cơ chế phát hiện xung đột (`obsidian-sync-map.json`), ghi báo cáo xung đột vào `.agents/knowledge/conflicts/` và dừng tiến trình yêu cầu người dùng chọn giải pháp.
- **Tập lệnh CLI**:
  - Bổ sung lệnh CLI `aiwf provider resolve obsidian` và `aiwf provider sync obsidian`.
  - Nâng cấp lệnh `aiwf provider add/edit/test obsidian` và `aiwf provider doctor` để hỗ trợ các tham số cấu hình mới.
- **Knowledge Runtime Integration**:
  - Tích hợp hàm `knowledge.sync(provider="obsidian")` vào Knowledge Runtime để tự động đồng bộ tài liệu dự án.

### Out of Scope
- Triển khai giao diện đồ họa (GUI) cho việc giải quyết xung đột bidirectional. Việc chọn hướng giải quyết xung đột sẽ được thực hiện thủ công hoặc qua dòng lệnh CLI.

## 3. Eligibility Matrix
- **Scope**: Single added feature set (Obsidian provisioning and syncing logic). (Eligible)
- **Architecture Impact**: Low/Medium (adds sync, slug resolution, and conflict report layers). (Eligible)
- **ADR Requirement**: No ADR required. (Eligible)
- **Estimated Work**: < 1 day. (Eligible)
