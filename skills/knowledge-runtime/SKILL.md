---
name: knowledge-runtime
command: knowledge
aliases:
  - rag
  - memory
category: runtime
tags:
  - runtime
  - knowledge
  - rag
  - cache
  - search
version: 1.0.0
license: MIT
created_at: 2026-07-09
updated_at: 2026-07-09
description: Unified knowledge layer and provider router for the AI Engineering Workflow framework.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: lazy
  rag: lazy
  workspace_scan: none
  environment: none
  version: none
  provider: optional
  usage: none---

# Knowledge Runtime Skill

## 1. Purpose
Thư viện tri thức hợp nhất giúp các đại lý/kỹ năng trong AIWF truy cập, tìm kiếm, lưu trữ thông tin dự án qua một cổng duy nhất, ngăn việc đọc file hoặc kết nối các provider thô trực tiếp.

## 2. Public APIs
Gói `knowledge_runtime` cung cấp các API công khai sau:
- `knowledge_runtime.search(query: str, limit: int = 5) -> list[dict]`
- `knowledge_runtime.read(path: str) -> str`
- `knowledge_runtime.save(path: str, content: str) -> bool`
- `knowledge_runtime.sync(provider: str = "obsidian") -> dict`

## 3. Workflow Integration
- **Before Hooks**: Nạp cấu hình hợp nhất (global + local overrides) qua `provider_manager`.
- **After Hooks**: Tự động dọn dẹp và làm mới bộ đệm cache khi ghi tệp.
- **Memory Interactions**: Truy vấn thông tin dự án thông qua Markdown Index.

## 4. Configuration
Cấu hình nhà cung cấp tri thức hỗ trợ hai cấp độ thông qua `provider_manager`:
1.  **Cấu hình toàn cục cấp máy** (`~/.aiwf/providers.json` trên Unix hoặc `%USERPROFILE%\.aiwf\providers.json` trên Windows):
    Lưu trữ cấu hình dùng chung và các api_key nhạy cảm. Ví dụ:
    ```json
    {
      "providers": {
        "obsidian": {
          "enabled": true,
          "mode": "file-sync",
          "vault_root": "/Users/user/Obsidian/Vault",
          "project_folder_pattern": "AIWF-Knowledge-{project_slug}",
          "create_if_missing": true,
          "sync_structure": true
        }
      }
    }
    ```
2.  **Cấu hình cục bộ dự án** (`.agents/memory.config.json`):
    Lưu trữ các cấu hình ghi đè cục bộ cho riêng dự án đó (như thay đổi mode hoặc tắt/bật nhà cung cấp).
    *   Hệ thống tự động giải quyết các biến môi trường dạng `${VAR}` có trong giá trị cấu hình.
    *   Mã khóa bí mật tự động được che giấu (`mask_secrets`) khi hiển thị thông tin hoặc ghi nhật ký.
    *   Tự động sinh project folder Obsidian con dạng `{vault_root}/{project_folder_pattern}/` dựa trên Git repo hoặc tên thư mục dự án để tách biệt hoàn toàn tri thức giữa các dự án.

## 5. Runtime Commands
- `aiwf knowledge provider list [--project]`
- `aiwf knowledge provider add <name> [--project]`
- `aiwf knowledge provider edit <name> [--project]`
- `aiwf knowledge provider remove <name> [--project]`
- `aiwf knowledge provider enable <name> [--project]`
- `aiwf knowledge provider disable <name> [--project]`
- `aiwf knowledge provider test <name> [--project]`
- `aiwf knowledge provider resolve <name>`
- `aiwf knowledge provider sync <name>`
- `aiwf knowledge provider doctor [name]`
- `aiwf knowledge provider path`

## 6. Provider Strategy
Hệ thống sử dụng Markdown Provider làm gốc bắt buộc. Nếu các provider tùy chọn (SQLite, Qdrant, Obsidian) không sẵn sàng hoặc bị vô hiệu hóa, hệ thống tự động đưa ra cảnh báo nhẹ và định tuyến ngược về Markdown Provider.
Obsidian Provider hỗ trợ các chế độ: `file-sync` (mặc định), `rest`, `readonly`, `bidirectional` (có tính năng kiểm tra xung đột timestamps/hashes trước khi ghi đè, lưu trữ báo cáo xung đột trong thư mục `.agents/knowledge/conflicts/`).

## 7. Backward Compatibility
Hỗ trợ adapter tương thích ngược cho các cuộc gọi RAG search cũ và tự động kế thừa cấu hình từ dự án cũ (như `vault_path`) nếu cấu hình toàn cục chưa nâng cấp lên `vault_root`.

## 8. Usage Examples
```python
from knowledge_runtime import search, read, sync
# Thực hiện tìm kiếm
results = search("project context")
content = read(results[0]["path"])

# Kích hoạt đồng bộ hóa Obsidian
sync_res = sync("obsidian")
print(sync_res)
```

## 9. Extension Points
Các Provider mới có thể dễ dàng bổ sung bằng cách kế thừa từ lớp `BaseProvider` trong `providers/base.py`.

## 10. Limitations
Hiện tại cache lưu cục bộ dạng JSON. Tương lai sẽ nâng cấp lên SQLite cache hoàn toàn.
