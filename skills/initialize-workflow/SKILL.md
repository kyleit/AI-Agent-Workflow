---
name: initialize-workflow
command: init
aliases:
  - initialize
category: runtime
tags:
  - initialization
  - runtime
  - lightweight
  - bootstrap
version: 3.4.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-31
bootstrap_role: MANDATORY_BOOTSTRAP_AUTHORITY
canonical_entrypoint_authority: false
wrapper_entrypoint: aiwf
delegates_to: workflow-coordinator
receipt_schema: skills/initialize-workflow/schemas/bootstrap-receipt.schema.json
receipt_template: skills/initialize-workflow/templates/bootstrap-receipt.md
receipt_config: skills/initialize-workflow/config/bootstrap-rules.yaml
description: Mandatory runtime bootstrap initializer for the AI Engineering Workflow. Resolves repository root via git rev-parse --show-toplevel, loads AI_RULES.md + AGENTS.md (all 13 global policies), loads .agents/state AND .agents/memory/walkthrough.md for full prior-session context, validates project identity & active workflow, checks duplicate workflow/orchestrator locks, and issues a SHA-256 validated Bootstrap Receipt.
runtime_requirements:
  rules: session_cached
  state: required
  approvals: required
  git: cached
  memory: session_cached
  rag: cached
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached
---

> [!CRITICAL]
> ## ⛔ AI AGENT: YOU MUST EXECUTE THIS SKILL COMPLETELY
>
> If you are reading this skill file, you are REQUIRED to execute the FULL
> Mandatory Bootstrap Execution Checklist (Section 4) BEFORE responding to the user.
>
> **DO NOT skip any step. DO NOT respond to the user before completing bootstrap.**
>
> If you have already completed bootstrap in this session (AI_RULES.md is in your context),
> use Mode B (Subsequent Call) to skip [CACHED] items only.
>
> **PHYSICAL WRITES ONLY**: All downstream implementation MUST use physical file writes.
> IDE "Apply" button, proposed changes, code blocks in chat are NOT valid implementation.
> Ref: Physical Repository Write Policy (AI_RULES.md Section 33)

# Skill: initialize-workflow (Mandatory AIWF Bootstrap Authority)

## 1. Role & Authority
`initialize-workflow` là cơ quan cấp phép và khởi tạo Bootstrap độc nhất của AIWF framework (`MANDATORY_BOOTSTRAP_AUTHORITY`). Mọi yêu cầu từ Wrapper Skill `aiwf` hay bất kỳ giao diện người dùng nào BẮT BUỘC phải thực thi `initialize-workflow` trước để tạo một **Bootstrap Receipt** hợp lệ trước khi được chuyển tiếp sang `workflow-coordinator`.

---

## 2. Core Bootstrap Responsibilities
1. **Repository Root Resolution**: Chạy `git rev-parse --show-toplevel` để tìm chính xác root repository. Cấm dùng shell current directory làm authority khi Git root tồn tại.
2. **State Authority Loading**: Đọc dữ liệu trạng thái từ `.agents/state` (`.agents/.session.json` là DEPRECATED và bị bỏ qua làm source of truth).
3. **Rules & Policy Loading**: Đọc và nắm vững toàn bộ rules **TRƯỚC KHI** thực hiện bất kỳ hành động nào. **BẮT BUỘC** đọc theo thứ tự:
   - `AI_RULES.md` — **PHẢI ĐỌC TRƯỚC TIÊN**: chứa 13 Global Policies (Approval Gate, Blueprint Mandatory Implementation, Git Workflow, Memory First, Script-First, Workflow First Enforcement...). Đây là single source of truth. File này PHẢI tồn tại — nếu không có, BLOCK bootstrap.
   - `AGENTS.md` — chứa Workflow Coordinator First Policy, Blueprint Approval Gate, Quick-fix eligibility, Agent Catalog. Thiếu file này → WARN và tiếp tục với caution.
   - **Lý do bắt buộc**: Thiếu bước này dẫn đến agent vi phạm §13 Blueprint Mandatory Policy, §1 Approval Gate Policy, §27 Workflow First Enforcement Policy ngay từ đầu session — gây ra các hành động trái phép như sửa file trực tiếp không qua Blueprint approval.
4. **Memory Context Loading**: Đọc toàn bộ memory context để biết rõ việc đang làm dở dang từ session trước. **BẮT BUỘC** đọc theo thứ tự ưu tiên:
   - `memory/walkthrough.md` — **PHẢI ĐỌC**: ghi lại việc đã hoàn thành và đang dở dang từ session trước. Nguồn context quan trọng nhất về tiến độ.
   - `state/walkthrough.md` — chi tiết changes của work item hiện tại (changes made, verification results, next steps).
   - `memory/project-summary.md` — tổng quan kiến trúc dự án.
   - `memory/memory-state.json` — kiểm tra freshness (last_updated_at, last_git_hash).
   - `inbox/inbox.json` — kiểm tra tin nhắn Telegram chờ xử lý. Nếu có → đọc và xử lý sau bootstrap.
   - `project-profile.json` — recommended workflow steps, tech stack, test/lint tools.
5. **Project Identity & Isolation**: Xác minh `project_id`, `repository_identity` và ngăn chặn việc đính kèm nhầm workflow giữa các dự án khác nhau (`PROJECT_IDENTITY_MISMATCH`).
6. **Duplicate Guard**: Kiểm tra xung đột duplicate active workflow hoặc duplicate orchestrator/session owner (`DUPLICATE_ACTIVE_WORKFLOW`, `DUPLICATE_ORCHESTRATOR`).
7. **Bootstrap Modes Handling**:
   - `NEW_REQUEST`: Khởi tạo workflow mới khi chưa có active workflow hoặc giữ nguyên raw request.
   - `RESUME`: Nạp lại active workflow, đối chiếu checkpoint và artifact hashes.
   - `STATUS_READ_ONLY`: Nạp trạng thái ở chế độ READ_ONLY, cấp receipt và không làm thay đổi trạng thái hay tạo workflow mới.
   - `HELP_READ_ONLY`: Nạp context ở chế độ READ_ONLY để gợi ý lệnh phù hợp, cấp receipt và không tự chạy lệnh.
   - `NEXT` / `CONTINUE` / `DEBUG` / `VERIFY`: Bootstrap đầy đủ trước khi coordinator thẩm định eligibility.
   - `CANCEL` / `RECOVER`: Xác minh identity trước khi thực thi chuyển trạng thái.
8. **Receipt Issuance**: Cấp tệp receipt tuân thủ `skills/initialize-workflow/schemas/bootstrap-receipt.schema.json` chứa mã băm đầy đủ SHA-256 (`content_hash`).
9. **Runtime-Supervised Telegram Only**: `initialize-workflow` KHÔNG được tự start Telegram daemon riêng. Nếu cần Telegram listener, chỉ được đảm bảo runtime daemon đang chạy (`runtime start` / runtime supervisor); Telegram worker do runtime supervisor quản lý.

---

## 3. Bootstrap Decisions
- `BOOTSTRAP_READY`: Khởi tạo/nạp thành công, đủ điều kiện cho luồng ghi/chuyển phase.
- `BOOTSTRAP_READY_READ_ONLY`: Nạp thành công cho các lệnh đọc (`status`, `help`).
- `BOOTSTRAP_BLOCKED`: Phát hiện xung đột, sai lệch identity, thiếu state hoặc checkpoint không hợp lệ. **Cũng BLOCK khi `AI_RULES.md` không tồn tại.**
- `BOOTSTRAP_INVALID`: Lỗi khởi tạo hệ thống.

---

## 4. Mandatory Bootstrap Execution Checklist

Agent PHẢI thực hiện **đúng thứ tự** các bước sau. Nhãn:
- `[CACHED]` — đọc 1 lần/session, **skip nếu đã có trong context window**
- `[REFRESH]` — luôn đọc lại mỗi lần bootstrap (có thể thay đổi trong session)

```
MANDATORY — Rules:
[CACHED]   1. Đọc AI_RULES.md                  → 13 Global Policies — BLOCK nếu thiếu file
[CACHED]   2. Đọc AGENTS.md                    → Workflow policies, Blueprint gate, Agent catalog

MANDATORY — State:
[REFRESH]  3. git rev-parse --show-toplevel    → xác định repository root tuyệt đối
[REFRESH]  4. Đọc state/workflow.json          → active work item, phase, checkpoint
[REFRESH]  5. Đọc state/context.json           → project_id, authorization, session
[REFRESH]  6. Đọc state/approvals.json         → blueprint/release approval status
[REFRESH]  7. Đọc state/active-work-items.json → stale work items registry

MANDATORY — Memory Context:
[CACHED]   8. Đọc memory/walkthrough.md        → việc đang làm dở dang từ session trước ★
[CACHED]   9. Đọc state/walkthrough.md         → chi tiết changes của work item hiện tại
[REFRESH] 10. Đọc memory/memory-state.json     → freshness check (last_git_hash có thể đổi)

MANDATORY — Runtime Signals:
[CACHED]  11. Đọc project-profile.json         → recommended workflow steps, tech stack
[REFRESH] 12. Đọc inbox/inbox.json             → Telegram messages chờ xử lý (real-time)
[REFRESH] 13. Kiểm tra orchestrator.json       → duplicate guard

→  Phát hành Bootstrap Receipt (SHA-256)
→  Chuyển tiếp sang workflow-coordinator
```

> [!IMPORTANT]
> **Bước 1-2 [CACHED]**: Nếu `AI_RULES.md` và `AGENTS.md` đã được đọc trước đó trong cùng session (đã có trong context window), agent **KHÔNG cần đọc lại** — tiết kiệm ~96KB token.
>
> **Bước 12 [REFRESH]**: `inbox/inbox.json` luôn phải check mỗi lần — Ba có thể gửi lệnh Telegram bất kỳ lúc nào trong session.
>
> **★ Files vắng (walkthrough, inbox) → skip gracefully với INFO log, không BLOCK bootstrap.**

---

## 5. Session Cache Behavior

Bootstrap hoạt động ở **2 mode** tùy theo trạng thái session:

### Mode A — First Call (Session mới)
Khi agent chưa load bất kỳ context nào trong session hiện tại:
- Thực hiện **đầy đủ 13 bước** theo checklist.
- Tất cả `[CACHED]` items được đọc và giữ trong context window cho các lần gọi sau.

### Mode B — Subsequent Call (Trong cùng session)
Khi `AI_RULES.md` và `AGENTS.md` đã có trong context window:
- **SKIP** bước `[CACHED]`: 1, 2, 8, 9, 11 — tiết kiệm ~110KB token.
- **BẮT BUỘC REFRESH** bước `[REFRESH]`: 3, 4, 5, 6, 7, 10, 12, 13.

### Bảng phân loại cache

| Bước | File | Mode | Lý do |
|------|------|------|-------|
| 1 | `AI_RULES.md` | CACHED | Static — không đổi trong session |
| 2 | `AGENTS.md` | CACHED | Static — không đổi trong session |
| 3 | `git rev-parse` | REFRESH | Branch có thể switch |
| 4 | `state/workflow.json` | REFRESH | Phase thay đổi theo tiến độ |
| 5 | `state/context.json` | REFRESH | Auth có thể update |
| 6 | `state/approvals.json` | REFRESH | Blueprint approval có thể được grant |
| 7 | `state/active-work-items.json` | REFRESH | Work items thay đổi |
| 8 | `memory/walkthrough.md` | CACHED | Không đổi trong session |
| 9 | `state/walkthrough.md` | CACHED | Không đổi trong session |
| 10 | `memory/memory-state.json` | REFRESH | Memory sync có thể chạy background |
| 11 | `project-profile.json` | CACHED | Static project config |
| 12 | `inbox/inbox.json` | REFRESH | Realtime Telegram messages |
| 13 | `orchestrator.json` | REFRESH | Lock state thay đổi |

