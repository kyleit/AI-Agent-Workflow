---
name: create-adr
command: adr
aliases:
  - architecture-decision
category: architecture
tags:
  - adr
  - architecture
  - decision
version: 2.5.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-03
description: Create Architecture Decision Records (ADRs) only when explicitly invoked.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: none---

# Skill: Create Architecture Decision Record (ADR)

## Purpose

This Skill is used to record and document critical architectural decisions and their trade-offs. It is invoked when `plan-to-blueprint` recommends an ADR, or when a developer determines a significant architecture decision is required.

It creates a dedicated ADR document under:
```text
docs/adr/ADR-XXX_short_title.md
```

This Skill does NOT generate source code, plans, or implementation designs.

---

## Role

You are acting as a **Principal Software Architect** and **Technical Authority**.

---

## Input

```yaml
title: "Decide on cache strategy for Playwright assets"
# Short title of the architecture decision (required)

related_feature: "docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_slug.md"
# Relative path to the related brainstorming or requirement discovery document

design_file: "docs/features/<feature-family>/blueprints/FEAT-XXX_feature_slug_blueprint.md"
# Relative path to the blueprint design (optional)
```

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "at least 1"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "create-adr" --command "adr" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ADR Numbering Rules

This Skill MUST follow the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before writing the ADR file.
- **Artifact Policy** (Section 5) - For generating ADRs under `docs/adr/` in `ADR-XXX_slug.md` format.

Calculate the next ADR ID by scanning `docs/adr/` as defined in Section 5 (Artifact Policy) of `AI_RULES.md`. If empty, start at `ADR-001`. Otherwise, use `highest_id + 1`.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

## Output Rules

Create exactly one file under `docs/adr/`:
```text
docs/adr/ADR-XXX_short_title.md
```
*(Replace `XXX` with the calculated ADR ID, and `short_title` with a clean, lowercase, underscore-separated slug, e.g., `docs/adr/ADR-001_cache_strategy.md`)*

The generated file must contain:

```markdown
<!-- File path: docs/adr/ADR-XXX_short_title.md -->

# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Rejected | Superseded]

## Related Feature
[FEAT-XXX (e.g. FEAT-001)]

## Context
[What is the context, problem description, and drivers of this decision?]

## Decision
[What is the selected option/architecture decision?]

## Alternatives Considered
[What alternative options were evaluated and rejected?]

## Trade-offs
[What are the pros and cons of the options considered?]

## Consequences
[What is the consequence of this decision on the codebase and future work?]

## Risks
[What risks does this decision introduce and how will they be mitigated?]

## References
[Links to related features, plans, designs, or external documentations]
```

---

## Capability Boundary & Guardrails

- **Allowed Output**: The Skill only owns and is allowed to write files under `docs/adr/` in the format `ADR-XXX_slug.md`.
- **No Code Modification**: The Skill must NEVER modify source code, configurations, tests, build scripts, or documentations outside `docs/adr/` as defined in [AI_RULES.md](../../AI_RULES.md).
- **No Downstream Tasks**: The Skill must NEVER generate plans, blueprints, or source code.
- **Independent Invocation**: Do NOT execute other skills automatically. Refer to [AI_RULES.md](../../AI_RULES.md) for pure workflow limits.

---

## Completion Contract

```text
Current Phase:
Architecture Decision Record (ADR) Creation

Status:
Completed

ADR Generated:
docs/adr/ADR-XXX_short_title.md

ADR ID:
ADR-XXX

Related Feature ID:
FEAT-XXX

Workflow Paused.
```

## Evaluation Criteria & Readiness Score (Scale 100)
Giai đoạn chỉ được qua cổng kiểm duyệt khi tổng điểm từ 95 trở lên và không vi phạm tiêu chí đường dẫn (đánh fail lập tức nếu vi phạm chính sách đường dẫn tuyệt đối).

| # | Tiêu chí đánh giá | Điểm tối đa | Điểm đạt | Điều kiện đạt đủ điểm & Ghi chú |
|---|---|---:|:---:|---|
| 1 | Tương thích đường dẫn | 30 | /30 | 100% đường dẫn trong mã nguồn, script, kết quả và tài liệu là đường dẫn tương đối hoặc đã được làm sạch. Không có URL tệp tuyệt đối, đường dẫn ổ đĩa, đường dẫn tuyệt đối của macOS hoặc Linux, mã xác thực hoặc log chứa đường dẫn tuyệt đối. |
| 2 | Build và chạy runtime thật | 20 | /20 | App, service, UI, CLI hoặc worker build lại thành công, runtime thật mở được, surface tích hợp thật sẵn sàng, và không còn tiến trình treo sau kiểm thử. |
| 3 | Kiểm thử runtime thật | 20 | /20 | Kiểm thử gọi vào runtime đang chạy qua surface thật phù hợp như IPC, API, UI, CLI, SDK, job queue hoặc service, không chỉ kiểm thử đơn vị hoặc phản chiếu. Luồng thành công chính, luồng lỗi hợp lệ, luồng hồi quy và dọn dẹp đều đạt. |
| 4 | Đầy đủ chức năng | 15 | /15 | Giai đoạn triển khai đủ lệnh hoặc API bắt buộc, không có phần giữ chỗ chưa hoàn thiện, không bỏ sót hành vi cũ quan trọng. |
| 5 | Dễ đọc và dễ bảo trì | 5 | /5 | Mã nguồn, script và kết quả rõ ràng, có cấu trúc, đặt tên dễ hiểu, ít trùng lặp và không lan phạm vi ngoài giai đoạn. |
| 6 | Tuân thủ rule, Memory/RAG và skill trong project | 5 | /5 | Người điều phối và tác nhân đã đọc rule trong project, ưu tiên Memory First/RAG First bằng `./.agents/skills/project-rag-search` khi cần ngữ cảnh, chọn skill phù hợp từ `./.agents/skills`, đọc hướng dẫn skill trước khi làm, ghi rule/skill trong prompt/báo cáo và không tạo bản rule hoặc skill trùng lặp ở nơi khác. |
| 7 | An toàn dữ liệu và dọn dẹp | 5 | /5 | Kiểm thử chụp nhanh và khôi phục cấu hình, không tạo rác ở Màn hình nền hoặc thư mục tạm, không lộ mã xác thực hoặc bí mật, không để lại tiến trình app hoặc kiểm thử. |
| | **Tổng điểm** | **100** | **/100** | **Điểm đạt tối thiểu để Release: 95/100** |

## Điều kiện bắt buộc đánh FAIL (NO-GO)
Giai đoạn phải bị đánh FAIL (NO-GO) nếu gặp bất kỳ lỗi nào dưới đây (điểm đánh giá bị vô hiệu):
1. Có đường dẫn tuyệt đối thật trong mã nguồn, script, kết quả hoặc tài liệu thuộc phạm vi giai đoạn.
2. Build thất bại.
3. Ứng dụng không mở được.
4. Surface tích hợp thật của runtime không sẵn sàng (ví dụ: IPC token/pipe, API endpoint, UI route, CLI command, SDK entrypoint hoặc service health).
5. Ca kiểm thử runtime chính thất bại.
6. Kiểm thử chỉ là kiểm thử đơn vị hoặc phản chiếu (reflection) mà chưa gọi vào runtime thật.
7. Có tiến trình app hoặc kiểm thử còn treo sau khi kiểm thử kết thúc.
8. Kết quả chứa mã xác thực, bí mật hoặc dữ liệu chưa được làm sạch.
9. Có luồng tự ý tắt app, service hoặc runtime trong khi luồng điều phối chính chưa cho phép.
10. Chưa đủ bằng chứng thực tế nhưng báo cáo đạt.
11. Bỏ qua các skill phù hợp sẵn có trong `./.agents/skills` mà không có lý do được chấp nhận.
12. Tự ý copy hoặc tạo bản sao skill, prompt hoặc workflow mới ở thư mục khác khi project đã có skill tương ứng.
13. Bỏ qua rule của project hoặc không chứng minh đã đọc rule bắt buộc.
14. Tạo rule song song làm lệch hướng `PROJECT_RULES.md`, `./.agents/AGENTS.md` hoặc `./.agents/AI_RULES.md`.
15. Quét mã nguồn hoặc hỏi thiết kế trước khi tra cứu Project Memory và dùng `./.agents/skills/project-rag-search` khi cần ngữ cảnh.
