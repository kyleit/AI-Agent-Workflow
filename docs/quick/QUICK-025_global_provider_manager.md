<!-- File path: docs/quick/QUICK-025_global_provider_manager.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-025
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Add Machine-Level Global Provider Manager for AIWF

| 🔒 QUICK-FEATURE MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the QUICK feature specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/quick/QUICK-025_global_provider_manager.md` |
| Design Blueprint path: `docs/designs/QUICK-025_global_provider_manager_blueprint.md` |

---

## 1. Feature Goal
Thiết lập bộ quản lý cấu hình nhà cung cấp tri thức ở cấp độ máy tính (Machine-Level Global Provider Manager) cho AIWF. Người dùng chỉ cần định nghĩa thông tin kết nối và khóa bí mật (`api_key` của Obsidian, Qdrant, OpenAI, v.v.) một lần duy nhất tại thư mục Home của máy (`~/.aiwf/providers.json`), sau đó mọi dự án AIWF trên máy tính đó đều có thể tự động kế thừa và sử dụng chung mà không cần khai báo lại hoặc lưu trữ khóa bí mật trong mã nguồn dự án.

## 2. Scope

### In Scope
- **Module Quản lý Toàn cục (`provider_manager.py`)**:
  - Xác định vị trí tệp cấu hình toàn cục: `~/.aiwf/providers.json` trên macOS/Linux và `%USERPROFILE%\.aiwf\providers.json` trên Windows.
  - Hỗ trợ nạp cấu hình toàn cục (`load_global_config`), lưu cấu hình (`save_global_config`), nạp cấu hình cục bộ dự án (`load_project_config` từ `.agents/memory.config.json`).
  - Hỗ trợ trộn cấu hình (`resolve_provider_config` & `resolve_all_providers`) theo quy tắc: Global Config -> Project Overrides.
  - Hỗ trợ biên dịch biến môi trường trong cấu hình (như `${OBSIDIAN_API_KEY}`).
  - Hỗ trợ che giấu mã khóa bảo mật (`mask_secrets`) trong kết xuất màn hình và báo cáo.
- **Tích hợp Knowledge Runtime**:
  - Cập nhật `knowledge-runtime` (tệp `api.py`) để gọi qua `provider_manager` lấy thông số cấu hình đã phân giải thay vì chỉ đọc tệp cục bộ `.agents/memory.config.json`.
- **Cấu hình Obsidian Toàn cục**:
  - Hỗ trợ các chế độ Obsidian: `file-sync` (mặc định), `rest`, `readonly`, `bidirectional`.
- **Bổ sung tập lệnh CLI (`aiwf provider ...`)**:
  - Thêm các lệnh con vào CLI của `workflow_runtime.py` phục vụ việc tương tác dòng lệnh:
    - `aiwf provider list` (liệt kê danh sách)
    - `aiwf provider add <name>` (thêm nhà cung cấp mới với đối thoại nhập dữ liệu)
    - `aiwf provider edit <name>` (chỉnh sửa thông tin)
    - `aiwf provider remove <name>` (xóa nhà cung cấp)
    - `aiwf provider enable/disable <name>` (bật/tắt trạng thái)
    - `aiwf provider test <name>` (chạy thử kết nối)
    - `aiwf provider doctor` (kiểm tra phân quyền bảo mật tệp cấu hình toàn cục)
    - `aiwf provider path` (in đường dẫn tệp cấu hình toàn cục)
- **Bảo mật**:
  - Đảm bảo tạo thư mục `~/.aiwf/` với phân quyền giới hạn người dùng (`0700` hoặc tương đương).
  - Không in khóa bí mật ra màn hình terminal hay log tệp tin.
- **Tài liệu**:
  - Cập nhật hướng dẫn trong: `README.md`, `AGENTS.md`, `AI_RULES.md`, `INSTALL.md`, `USAGE.md`, `skills/knowledge-runtime/SKILL.md`, `skills/project-memory-update/SKILL.md`.

### Out of Scope
- Triển khai thêm các Provider lưu trữ dữ liệu đám mây mới ngoài Obsidian, SQLite và Qdrant.

## 3. Eligibility Matrix
- **Scope**: Single added capability (Global Provider config merging layer). (Eligible)
- **Architecture Impact**: Low/Medium (adds fallback and merge flow, fully backward-compatible). (Eligible)
- **ADR Requirement**: No ADR required. (Eligible)
- **Estimated Work**: < 1 day. (Eligible)
