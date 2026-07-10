<!-- File path: docs/designs/FEAT-017_environment_checks_caching_blueprint.md -->

---
feature_id: FEAT-017
feature_name: Environment Checks Caching and Option Selection Policy
status: proposed
stage: blueprint
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../plans/FEAT-017_environment_checks_caching_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint – Environment Checks Caching and Option Selection Policy (FEAT-017)

## 0. Project Memory Baseline
- **Tài liệu tham chiếu chính**:
  - [AI_RULES.md](file:///Volumes/Kyle/AgentsProject/.agents/AI_RULES.md)
  - [SKILL.md](file:///Volumes/Kyle/AgentsProject/.agents/skills/initialize-workflow/SKILL.md)

## 1. Specification of env_cache.json
Tệp tin cache môi trường sẽ được lưu tại `.agents/runtime/env_cache.json` với cấu trúc JSON như sau:
```json
{
  "cached_at": "ISO-8601 Timestamp (e.g., 2026-07-07T14:48:25+07:00)",
  "tools": {
    "git": "available | missing",
    "python": "available | missing",
    "node": "available | missing",
    "go": "available | missing",
    "docker": "available | missing",
    "tree-sitter": "available | missing",
    "qdrant": "available | missing",
    "qmd": "available | missing",
    "ollama": "available | missing"
  }
}
```

## 2. Policy Changes Specification

### A. AI_RULES.md
1. **Section 17 (Environment Tools Checking and Caching Policy)**:
   - Các Agent bắt buộc ghi nhận trạng thái kiểm tra vào `.agents/runtime/env_cache.json`.
   - Nếu tệp tồn tại và thời gian lưu (`cached_at`) chưa quá 24h, Agent bắt buộc phải bỏ qua việc chạy các lệnh shell kiểm tra và tải kết quả trực tiếp từ cache.
2. **Section 18 (Option Selection and Decision Making Policy)**:
   - Các Agent bắt buộc sử dụng công cụ `ask_question` để hiển thị menu tương tác cho Ba khi đề xuất nhiều phương án lựa chọn, không được chỉ liệt kê dạng văn bản thuần túy.

### B. initialize-workflow SKILL.md
- Cập nhật Step 9 để kiểm tra và xử lý logic đọc từ tệp cache `.agents/runtime/env_cache.json` trước khi thực thi lệnh shell.

## 3. Verification Plan
- Xác minh tính toàn vẹn của tệp cấu trúc JSON `.session.json` và `env_cache.json`.
