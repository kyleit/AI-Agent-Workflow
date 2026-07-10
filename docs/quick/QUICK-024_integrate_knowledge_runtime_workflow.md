<!-- File path: docs/quick/QUICK-024_integrate_knowledge_runtime_workflow.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-024
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Integrate knowledge-runtime Across the Entire AIWF Workflow

## 1. Feature Goal
Chuyển đổi `knowledge-runtime` thành tầng giao tiếp tri thức duy nhất của toàn bộ hệ thống AIWF. Mọi kỹ năng và đại lý khi cần tìm kiếm, đọc, lưu trữ thông tin đều bắt buộc phải đi qua API của `knowledge-runtime` thay vì đọc Markdown trực tiếp hoặc gọi trực tiếp tới các Provider như SQLite, Qdrant hay Obsidian.

## 2. Scope
- **In Scope**:
  - Tạo tệp tin [skills/knowledge-runtime/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/SKILL.md) đầy đủ 10 phần mô tả cấu trúc (Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations).
  - Di chuyển tệp kiểm thử từ `skills/workflow-runtime/tests/test_knowledge_runtime.py` sang [skills/knowledge-runtime/tests/test_knowledge_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/tests/test_knowledge_runtime.py) để tuân thủ cấu trúc Skeleton bắt buộc mới của QUICK-023.
  - Cập nhật tệp [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/AI_RULES.md):
    - Bổ sung quy tắc: "No AIWF Skill may access knowledge providers directly. All knowledge operations must go through Knowledge Runtime unless explicitly approved as a compatibility adapter."
  - Cập nhật tệp [AGENTS.md](file:///Volumes/Kyle/AgentsProject/AGENTS.md) và [README.md](file:///Volumes/Kyle/AgentsProject/README.md) để khẳng định `knowledge-runtime` là tầng trừu tượng tri thức chính thức.
- **Out of Scope**: Viết lại toàn bộ mã nguồn của RAG search cũ. Chỉ cần tích hợp adapter nếu cần.
