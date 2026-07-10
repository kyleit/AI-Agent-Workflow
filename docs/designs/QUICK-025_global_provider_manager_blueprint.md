<!-- File path: docs/designs/QUICK-025_global_provider_manager_blueprint.md -->
---
artifact_type: technical-blueprint
feature_id: QUICK-025
workflow: quick-feature
status: pending
---
# Technical Design Blueprint – Add Machine-Level Global Provider Manager for AIWF

## 1. Complete Class & Module Design

### Module `provider_manager.py`
Nằm tại `skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py`.

#### Public APIs:
1.  `get_global_config_path() -> str`:
    *   macOS / Linux: `~/.aiwf/providers.json`
    *   Windows: `%USERPROFILE%\.aiwf\providers.json`
2.  `load_global_config() -> dict`:
    *   Tải cấu hình toàn cục. Nếu tệp không tồn tại, trả về `{"providers": {}}`.
    *   Nếu thư mục `~/.aiwf/` chưa có, tự động tạo mới với phân quyền chỉ người dùng (`0o700`).
3.  `save_global_config(config: dict) -> bool`:
    *   Lưu cấu hình toàn cục. Đảm bảo ghi đè an toàn và đặt phân quyền tệp là `0o600`.
4.  `load_project_config(project_root: str = ".") -> dict`:
    *   Tải cấu hình cục bộ từ `<project_root>/.agents/memory.config.json`. Trả về `{"providers": {}}` nếu không tồn tại.
5.  `resolve_provider_config(name: str, project_root: str = ".") -> dict`:
    *   Trộn cấu hình theo thứ tự: Global Config -> Project Overrides.
    *   Giải quyết biến môi trường dạng `${VAR}` bằng `os.path.expandvars`.
6.  `resolve_all_providers(project_root: str = ".") -> dict`:
    *   Trộn và trả về cấu hình của toàn bộ các nhà cung cấp.
7.  `list_providers(project_root: str = ".") -> dict`:
    *   Liệt kê danh sách các nhà cung cấp và trạng thái enabled của chúng sau khi resolve.
8.  `test_provider(name: str, project_root: str = ".") -> dict`:
    *   Kiểm tra tính kết nối của nhà cung cấp (ví dụ: gửi request thử đến Obsidian REST API nếu ở chế độ `rest`).
9.  `enable_provider(name: str) -> bool`:
    *   Bật trạng thái `enabled: true` trong tệp cấu hình toàn cục.
10. `disable_provider(name: str) -> bool`:
    *   Tắt trạng thái `enabled: false` trong tệp cấu hình toàn cục.
11. `mask_secrets(config: dict) -> dict`:
    *   Ẩn mã hóa các khóa nhạy cảm (thay thế bằng `********`).

---

## 2. CLI Command Structure

Bổ sung lệnh con `provider` vào `workflow_runtime.py`:

```bash
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider list [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider add obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider edit obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider remove obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider enable obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider disable obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider test obsidian [--project]
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider doctor
python3 skills/workflow-runtime/scripts/workflow_runtime.py provider path
```

---

## 3. Obsidian Global Provider Integration

*   **Chế độ `file-sync` (Mặc định)**: Thao tác đọc/ghi trực tiếp vào `vault_path` trên đĩa cục bộ thông qua MarkdownProvider. Không yêu cầu chạy Obsidian REST API.
*   **Chế độ `rest`**: Gửi truy vấn HTTP đến Obsidian Local REST API sử dụng `host`, `port` và `api_key`.
*   **Chế độ `readonly`**: Chặn mọi hành vi `save` hoặc ghi tài liệu, trả về cảnh báo hoặc `False`.
*   **Chế độ `bidirectional`**: Đọc so sánh thời gian thay đổi tệp tin (timestamp) hoặc giá trị băm (hash) để phát hiện xung đột trước khi ghi đè, tránh mất mát dữ liệu.

---

## 4. Proposed Changes

#### [NEW] [provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py)
*   Triển khai toàn bộ logic quản lý, lưu trữ, trộn và ẩn cấu hình.

#### [MODIFY] [api.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/api.py)
*   Thay thế việc đọc trực tiếp cấu hình cục bộ bằng việc nạp qua `provider_manager.resolve_all_providers()`.

#### [MODIFY] [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
*   Đăng ký parser và ánh xạ các lệnh `provider` tới các hàm thực thi trong `provider_manager.py`.

#### [NEW] [test_provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/tests/test_provider_manager.py)
*   Unit tests kiểm tra toàn bộ các kịch bản trộn, che giấu khóa bí mật và hoạt động CLI.

---

## 5. Verification Plan

### Automated Tests
- Chạy bộ unit tests mới:
  ```bash
  pytest skills/knowledge-runtime/tests/test_provider_manager.py
  ```

### Manual Verification
1.  Tạo tệp cấu hình toàn cục `~/.aiwf/providers.json`.
2.  Mở hai dự án AIWF khác nhau trên cùng máy và kiểm tra xem cả hai dự án đều nhận diện Obsidian api_key từ cấu hình toàn cục.
3.  Vô hiệu hóa Obsidian ở mức dự án A và kiểm tra xem dự án B vẫn hoạt động bình thường.
