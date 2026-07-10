<!-- File path: docs/designs/QUICK-026_global_obsidian_vault_root_provisioning_blueprint.md -->
---
artifact_type: technical-blueprint
feature_id: QUICK-026
workflow: quick-feature
status: pending
---
# Technical Design Blueprint – Add Global Obsidian Vault Root and Per-Project Folder Auto-Provisioning

## 1. Complete Class & Module Design

### Module `provider_manager.py`
Bổ sung các hàm sau để quản lý cấp phát và đồng bộ Obsidian:

1.  `resolve_obsidian_project_folder(project_root: str = ".") -> str`:
    *   Tải cấu hình Obsidian từ `resolve_provider_config("obsidian", project_root)`.
    *   Đọc tệp ánh xạ `.agents/knowledge/obsidian-project-map.json`.
    *   Nếu tệp ánh xạ tồn tại:
        *   So sánh `vault_root` toàn cục mới với `vault_root` trong ánh xạ. Nếu khác nhau, tính toán lại `resolved_path` dưới `vault_root` mới và lưu lại.
        *   Kiểm tra nếu thư mục tồn tại. Nếu `create_if_missing` là True và thư mục chưa có, tạo cấu hình thư mục mặc định.
    *   Nếu tệp ánh xạ chưa tồn tại:
        *   Nhận diện tên dự án theo độ ưu tiên:
            1.  `.agents/memory.config.json` -> `project_id`
            2.  `.agents/project-profile.json` -> `name` / `id`
            3.  Tên thư mục gốc chứa Git.
            4.  Tên thư mục hiện tại của workspace.
        *   Tạo `project_slug` sạch: chuyển chữ thường, thay thế ký tự đặc biệt/khoảng trắng bằng `-`, loại bỏ ký tự phân tách trùng lặp/thừa.
        *   Áp dụng mẫu đặt tên `project_folder_pattern` (mặc định: `AIWF-Knowledge-{project_slug}`).
        *   Phòng chống Path Traversal: Đảm bảo tên thư mục không chứa `..` hay các ký tự đặc biệt định tuyến. Đường dẫn kết quả phải nằm hoàn toàn trong `vault_root` (kiểm tra qua `os.path.commonpath`).
        *   Kiểm tra xung đột: Nếu thư mục đã tồn tại trên đĩa, đọc tệp `README.md` của thư mục đó. Nếu có Project Slug khác trong README, ném lỗi xung đột `ValueError`.
        *   Nếu `create_if_missing` là True: Tạo cấu trúc thư mục con (`Brainstorming`, `Plans`, `Blueprints`, `ADR`, `Memory`, `Releases`, `Lessons`, `Patterns`, `Assets`, `Indexes`) và tệp `README.md` tổng quan dự án.
        *   Lưu ánh xạ mới vào `.agents/knowledge/obsidian-project-map.json`.
    *   Trả về `resolved_path`.

2.  `sync_obsidian(project_root: str = ".") -> dict`:
    *   Giải quyết đường dẫn thư mục dự án qua `resolve_obsidian_project_folder(project_root)`.
    *   Lấy cấu hình `folder_mapping` (mặc định hoặc từ cấu hình).
    *   Nạp bộ ghi nhớ đồng bộ từ `.agents/knowledge/obsidian-sync-map.json`.
    *   Quét toàn bộ các tệp tin trong các thư mục được ánh xạ.
    *   So sánh mã băm MD5 của tệp tin nguồn (AIWF) và tệp tin đích (Obsidian).
    *   **Chế độ Sync**:
        *   `readonly`: Không bao giờ ghi vào Obsidian. Chỉ đọc/tìm kiếm.
        *   `file-sync` (Mặc định): Ghi tệp trực tiếp từ AIWF sang Obsidian, cập nhật hash.
        *   `rest`: Gửi cập nhật thông qua Obsidian REST API.
        *   `bidirectional`:
            *   Nếu cả hai tệp đều thay đổi so với lần đồng bộ trước (xung đột): Lưu báo cáo xung đột vào `.agents/knowledge/conflicts/<filename>.json` và bỏ qua tệp tin đó.
            *   Nếu chỉ một bên thay đổi: Thực hiện đồng bộ chéo tương ứng.
    *   Lưu lại trạng thái đồng bộ mới và trả về thống kê kết quả.

---

## 2. CLI Command Structure

Bổ sung các lệnh con mới của `provider`:

```bash
# Phân giải thư mục Obsidian của dự án hiện tại
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider resolve obsidian

# Thực hiện đồng bộ tài liệu sang Obsidian
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider sync obsidian
```

*   Lệnh `resolve obsidian` hiển thị chi tiết: `global config path`, `vault_root`, `project slug`, `resolved project folder`, `exists status`, `sync mode` và thông tin bảo mật.
*   Cập nhật đối thoại dòng lệnh `provider add/edit obsidian` để hỏi thêm: `vault_root`, `project_folder_pattern`, `create_if_missing`, `sync_structure`.

---

## 3. Proposed Changes

#### [MODIFY] [provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py)
*   Thêm logic phân giải thư mục Obsidian, tự động khởi tạo cấu trúc thư mục con, phát hiện xung đột sở hữu và xử lý đồng bộ tệp tin.

#### [MODIFY] [api.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/api.py)
*   Bổ sung phương thức `sync(provider="obsidian")` gọi qua `provider_manager.sync_obsidian()`.

#### [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
*   Đăng ký các lệnh con `resolve` và `sync` cho parser `provider`.

#### [MODIFY] [test_provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/tests/test_provider_manager.py)
*   Viết thêm Unit Tests kiểm tra tính tương thích ngược của `vault_path`, chống path traversal, tạo slug, đồng bộ, và phát hiện xung đột khi hai dự án dùng chung một `vault_root`.

---

## 4. Verification Plan

### Automated Tests
- Chạy toàn bộ các ca kiểm thử mới:
  ```bash
  pytest skills/knowledge-runtime/tests/test_provider_manager.py
  ```

### Manual Verification
1.  Định nghĩa `vault_root` toàn cục.
2.  Chạy `resolve obsidian` và kiểm tra thư mục Obsidian con tương ứng được tạo tự động với đầy đủ cấu trúc và tệp `README.md`.
3.  Chạy thử `sync obsidian` ở chế độ `file-sync` để đảm bảo tài liệu được chép sang Obsidian chính xác.
4.  Cố ý chỉnh sửa tệp ở cả hai nơi để kiểm tra khả năng phát hiện xung đột và ghi báo cáo ở chế độ `bidirectional`.
