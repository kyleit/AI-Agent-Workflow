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
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-09
updated_at: 2026-07-09
description: Unified knowledge layer and provider router for the AI Engineering Workflow framework.
---

# Knowledge Runtime Skill

## 1. Purpose
Thư viện tri thức hợp nhất giúp các đại lý/kỹ năng trong AIWF truy cập, tìm kiếm, lưu trữ thông tin dự án qua một cổng duy nhất, ngăn việc đọc file hoặc kết nối các provider thô trực tiếp.

## 2. Public APIs
Gói `knowledge_runtime` cung cấp các API công khai sau:
- `knowledge_runtime.search(query: str, limit: int = 5) -> list[dict]`
- `knowledge_runtime.read(path: str) -> str`
- `knowledge_runtime.save(path: str, content: str) -> bool`

## 3. Workflow Integration
- **Before Hooks**: Nạp cấu hình từ `.agents/memory.config.json`.
- **After Hooks**: Tự động dọn dẹp và làm mới bộ đệm cache khi ghi tệp.
- **Memory Interactions**: Truy vấn thông tin dự án thông qua Markdown Index.

## 4. Configuration
Tệp cấu hình tại `.agents/memory.config.json`:
- `active_provider`: `markdown` (mặc định) | `sqlite` | `vector_db` | `obsidian`
- `cache_enabled`: `true` (mặc định) | `false`
- `cache_ttl`: `600` (giây)

## 5. Runtime Commands
- `python workflow_runtime.py knowledge search "<query>"`

## 6. Provider Strategy
Hệ thống sử dụng Markdown Provider làm gốc bắt buộc. Nếu các provider tùy chọn (SQLite, Qdrant, Obsidian) không sẵn sàng, hệ thống tự động đưa ra cảnh báo nhẹ và định tuyến ngược về Markdown Provider.

## 7. Backward Compatibility
Hỗ trợ adapter tương thích ngược cho các cuộc gọi RAG search cũ.

## 8. Usage Examples
```python
from knowledge_runtime import search, read
results = search("project context")
content = read(results[0]["path"])
```

## 9. Extension Points
Các Provider mới có thể dễ dàng bổ sung bằng cách kế thừa từ lớp `BaseProvider` trong `providers/base.py`.

## 10. Limitations
Hiện tại cache lưu cục bộ dạng JSON. Tương lai sẽ nâng cấp lên SQLite cache hoàn toàn.
