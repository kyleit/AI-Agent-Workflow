<!-- File path: docs/designs/FIX-024_missing_obsidian_folder_mappings_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-024
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Missing Obsidian Folder Mappings

Bản thiết kế kỹ thuật sửa lỗi thiếu cấu hình đồng bộ hóa các thư mục tài liệu tri thức (`quick`, `issues`, `prompts`, `verification`, `debug`, `archive`) sang Obsidian.

## 1. Proposed Code Changes

### [skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py)
- **Operation**: MODIFY
- **Responsibility**: Quản lý các logic đồng bộ tri thức cho các Provider (bao gồm Obsidian).
- **Changes**:
  - Cập nhật từ điển `folder_mapping` mặc định (tại dòng 515-524) để thêm 6 cấu hình ánh xạ tri thức mới:
    ```python
    folder_mapping = obs_cfg.get("folder_mapping", {
        "docs/brainstorming": "Brainstorming",
        "docs/plans": "Plans",
        "docs/quick": "Brainstorming",
        "docs/issues": "Plans",
        "docs/designs": "Blueprints",
        "docs/adr": "ADR",
        "docs/releases": "Releases",
        ".agents/memory": "Memory",
        "lessons": "Lessons",
        "patterns": "Patterns",
        "docs/prompts": "Prompts",
        "docs/verification": "Verification",
        "docs/debug": "Debug",
        "docs/archive": "Archive"
    })
    ```

### [.agents/memory.config.json](file:///Volumes/Kyle/AgentsProject/.agents/memory.config.json)
- **Operation**: MODIFY
- **Responsibility**: Cấu hình bộ nhớ và tích hợp nhà cung cấp tri thức cho dự án.
- **Changes**:
  - Cập nhật cấu hình `"folder_mapping"` trong `"obsidian"` để thêm các thư mục tri thức mới đồng bộ sang Obsidian:
    ```json
      "folder_mapping": {
        "docs/brainstorming": "Brainstorming",
        "docs/plans": "Plans",
        "docs/quick": "Brainstorming",
        "docs/issues": "Plans",
        "docs/designs": "Blueprints",
        "docs/adr": "ADRs",
        "docs/releases": "Releases",
        ".agents/memory": "Project Memory",
        "lessons": "Lessons",
        "patterns": "Patterns",
        "docs/prompts": "Prompts",
        "docs/verification": "Verification",
        "docs/debug": "Debug",
        "docs/archive": "Archive"
      }
    ```

---

## 2. Target Folder Structure
Giữ nguyên cấu trúc thư mục hiện tại của hệ thống.

---

## 3. Interface & Data Contracts
Không thay đổi hợp đồng giao tiếp API hay CLI.

---

## 4. Algorithms & Key Logic
Khi hàm `sync_obsidian` được gọi, nó sẽ duyệt qua từ điển `folder_mapping` và thực hiện đồng bộ hóa tuần tự từng thư mục nguồn trong dự án sang các thư mục đích trong vault Obsidian của Ba, đảm bảo các tài liệu Spec QUICK và FIX được đặt đúng vị trí.

---

## 5. Validation Rules
- Đảm bảo các đường dẫn của thư mục nguồn tồn tại trong workspace trước khi thực hiện đồng bộ. Nếu không tồn tại, chỉ in log warning và tiếp tục.

---

## 6. Implementation Checklist
- [ ] Cập nhật `provider_manager.py` với cấu hình default `folder_mapping` mới.
- [ ] Cập nhật `.agents/memory.config.json` với cấu hình `folder_mapping` mới.
- [ ] Đồng bộ hóa framework bằng `./update.sh --force`.
- [ ] Cập nhật Project Memory để kiểm tra hoạt động đồng bộ tự động.

---

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Chạy đồng bộ Obsidian thành công, kiểm tra các tệp tin Spec QUICK và FIX xuất hiện chính xác trên Obsidian ở đúng các thư mục `Brainstorming` và `Plans`.
  - *REQ-002*: Chạy `pytest` đảm bảo toàn bộ unit tests hoạt động bình thường.
