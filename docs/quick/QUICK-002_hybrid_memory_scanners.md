<!-- File path: docs/quick/QUICK-002_hybrid_memory_scanners.md -->

---
artifact_type: quick-feature
feature_id: QUICK-002
workflow: quick-feature
architecture_impact: low
adr_required: true
status: PASS
---


# Mini Feature Specification – Tích hợp cơ chế Hybrid (CLI Script-First + LLM Contextual Polishing) vào quy trình bộ nhớ

## 1. Feature Goal
Bổ sung cơ chế phối hợp thông minh Hybrid giữa việc thực thi của Python CLI script (quét mã nguồn, ghi chỉ mục) và sự nhận thức của LLM Agent (bổ sung/điền đầy mô tả nghiệp vụ của các module và công nghệ trong `project-summary.md` sau khi CLI hoàn tất).

## 2. Business Value
Giúp tạo ra tài liệu tóm tắt dự án `project-summary.md` có chất lượng ngữ nghĩa và mức độ đọc hiểu nghiệp vụ cao nhất, trong khi vẫn duy trì được tốc độ quét siêu tốc và sự chính xác cấu trúc dữ liệu của cấu trúc Script-First.

## 3. Existing Context
- [ADR-002](file:///Volumes/Kyle/AgentsProject/docs/adr/ADR-002_hybrid_memory_scanners.md): Quyết định kiến trúc Hybrid.
- [skills/project-memory-bootstrap/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/project-memory-bootstrap/SKILL.md): Tệp chỉ dẫn kỹ năng bootstrap hiện tại.
- [skills/project-memory-update/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/project-memory-update/SKILL.md): Tệp chỉ dẫn kỹ năng update hiện tại.

## 4. Scope
- **In Scope**:
  - Bổ sung bước chỉ dẫn `"LLM Contextual Polishing"` vào tệp `SKILL.md` của cả hai kỹ năng `project-memory-bootstrap` và `project-memory-update` (cả bản gốc và bản cài đặt dưới `.agents/`).
  - Hướng dẫn rõ LLM Agent cách đọc file tóm tắt trung gian và điền thêm các thông tin mô tả chi tiết cho các module chính trong dự án.
- **Out of Scope**: Không thay đổi logic chạy của các script Python bên trong `runtime/scripts/project_memory/`.

## 5. Expected Files
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [skills/project-memory-bootstrap/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/project-memory-bootstrap/SKILL.md) | Thêm chỉ thị làm mịn tài liệu tóm tắt ban đầu |
| Modify | [.agents/skills/project-memory-bootstrap/SKILL.md](file:///Volumes/Kyle/AgentsProject/.agents/skills/project-memory-bootstrap/SKILL.md) | Thêm chỉ thị làm mịn tài liệu tóm tắt cục bộ |
| Modify | [skills/project-memory-update/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/project-memory-update/SKILL.md) | Thêm chỉ thị cập nhật mô tả nghiệp vụ tăng cường |
| Modify | [.agents/skills/project-memory-update/SKILL.md](file:///Volumes/Kyle/AgentsProject/.agents/skills/project-memory-update/SKILL.md) | Thêm chỉ thị cập nhật mô tả nghiệp vụ tăng cường cục bộ |

## 6. Proposed Changes

### Thay đổi chung cho các tệp `SKILL.md` của Bootstrap và Update
Thêm phần quy định **"LLM Contextual Polishing"**:
1.  Sau khi chạy kịch bản CLI Python hoàn tất thành công, LLM Agent **MUST** mở tệp `.agents/memory/project-summary.md` vừa được tạo ra/cập nhật.
2.  LLM Agent sử dụng khả năng đọc hiểu ngữ cảnh của mình để bổ sung thông tin chi tiết vào các cột mô tả trong bảng `## Main Modules` và mục `## Frameworks & Libraries`.
3.  **Ràng buộc an toàn**: LLM Agent không được thay đổi các cột chỉ mục hoặc khóa cấu trúc do script tạo ra, chỉ được ghi bổ sung nội dung mô tả văn bản để tránh phá vỡ cú pháp.
