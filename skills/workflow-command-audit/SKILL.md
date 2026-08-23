---
name: workflow-command-audit
description: "Canonical command-receipt persistence authority for AIWF. Use after a delegated command completes to validate the sanitized Command Receipt, reject any remaining absolute paths, compute and verify its SHA-256 content hash, atomically persist it under .agents/state/audit/commands/, and advance the tamper-evident receipt chain pointer at .agents/state/audit/latest-command.json."
command: audit-command
aliases:
  - command-audit
category: audit
tags:
  - audit
  - command-receipt
  - persistence
  - tamper-evident
version: 3.16.0
license: MIT
repository: https://gitlab.com/your-org/ai-workflow-skills
created_at: 2026-07-29
updated_at: 2026-07-29
canonical_entrypoint: false
user_invokable: false
role: WORKFLOW_COMMAND_AUDIT_PERSISTENCE
state_authority: .agents/state
receipt_path_pattern: .agents/state/audit/commands/YYYY/MM/DD/<command-id>.json
latest_pointer_path: .agents/state/audit/latest-command.json
path_base: REPOSITORY_ROOT
repository_root_representation: "."
allow_absolute_paths: false
hash_algorithm: SHA-256
---

# Skill: workflow-command-audit (Canonical Command Audit Persistence Authority)

## 1. Overview & Role
Skill `workflow-command-audit` là cơ quan quản lý và ghi nhận tệp chứng minh lệnh (Command Receipt) độc nhất của AIWF framework (`WORKFLOW_COMMAND_AUDIT_PERSISTENCE`).

Nhiệm vụ duy nhất:
1. Thẩm định tệp Command Receipt đã được làm sạch đường dẫn tuyệt đối (Sanitized Command Receipt).
2. Kiểm tra `absolute_paths_remaining == 0`. Lập tức từ chối và hủy ghi nếu còn đường dẫn tuyệt đối (`PATH_SANITIZATION_FAILED`).
3. Tính toán và xác minh mã băm đầy đủ SHA-256 (`content_hash`) sau khi làm sạch đường dẫn.
4. Ghi nguyên tử (Atomic write) tệp receipt vào chuỗi chứng minh lưu trữ tại `.agents/state/audit/commands/YYYY/MM/DD/<command-id>.json`.
5. Cập nhật con trỏ `latest-command.json` tại `.agents/state/audit/latest-command.json` theo cơ chế tamper-evident receipt chain (`previous_command_receipt_sha256`).

---

## 2. Command Completion Flow
```text
aiwf
→ initialize-workflow
→ bootstrap receipt
→ workflow-coordinator
→ delegated command execution
→ terminal command result
→ path sanitization (convert all absolute paths to repository-relative)
→ workflow-command-audit (Validate & Atomic Persist)
→ update latest-command pointer (.agents/state/audit/latest-command.json)
→ return user-facing response
```

Lệnh KHÔNG ĐƯỢC báo hoàn tất trước khi Command Receipt được ghi nhận và xác minh thành công.

---

## 3. Path Sanitization Rules
- **Repository Paths**: Chuyển đổi toàn bộ đường dẫn bên trong repository thành dạng tương đối POSIX từ Git root (ví dụ `skills/aiwf/SKILL.md`).
- **Repository Root Representation**: `repository_root = "."`, `path_base = "REPOSITORY_ROOT"`.
- **External Path Aliasing**: Thay thế tiền tố đường dẫn ngoài bằng alias chuẩn: `<HOME>`, `<WORKSPACE_ROOT>`, `<TEMP_DIR>`, `<CACHE_DIR>`, `<RUNTIME_DIR>`, `<UNKNOWN_EXTERNAL_PATH>`.
- **Zero Machine Path Leakage**: CẤM hiển thị hoặc persist `/Users/...`, `/home/...`, `/Volumes/...`, `C:\...`, `file:///...`.
