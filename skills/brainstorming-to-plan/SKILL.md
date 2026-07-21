---
name: brainstorming-to-plan
command: plan
aliases:
  - planning
  - planning-phase
category: workflow
tags:
  - planning
  - workflow
  - scoping
version: 3.2.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-09
description: Convert a structured master brainstorming document into a formal Execution Plan (Markdown & JSON) using a Memory-First strategy and the FEAT-XXX Feature ID format.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: cached---

# Skill: Planning Prompt → Implementation Plan (FEAT-XXX format)

## Purpose

Execute a planning prompt from a master brainstorming document and generate a complete, production-ready Implementation Plan under `docs/plans/`.

This Skill must NOT generate:
- Technical Blueprint (Design)
- Architecture Decision Records (ADRs)
- Source code
- Tests

Its only responsibility is creating the implementation planning document.

---

## Role

You are acting as a **Senior Software Architect**, **Technical Planner**, and **System Analyst**.

Your responsibility is to produce a production-ready Implementation Plan with the **lowest possible token usage** by reading memory before reading source code.

---

## Input

```yaml
# Structure-mirroring rule (applies in ANY project): a feature's brainstorming input may be either
#   (a) a single flat file:   docs/brainstorming/FEAT-XXX_feature_slug.md
#   (b) a multi-phase folder: docs/brainstorming/<feature-slug>/master/FEAT-XXX_..._master_brainstorming.md
#                              + docs/brainstorming/<feature-slug>/phase-NN-<phase-slug>/phase-brainstorming.md
# Detect which shape exists for this feature and mirror that same shape for the plan output.
prompt_file: docs/brainstorming/FEAT-XXX_feature_slug.md   # or the (b) folder form above
# Path to the brainstorming/requirement discovery file(s) containing the planning prompt

workspace: auto

language: auto

framework: auto

architecture: auto

output_path: docs/plans/   # mirrors prompt_file's shape — see Step 1
```

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 3 or 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "brainstorming-to-plan" --command "plan" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "plan-to-blueprint" --next-command "blueprint"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

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

# Workflow

## Step 1 — Read Master Requirement Document
First detect the shape of this feature's brainstorming input: a single flat `docs/brainstorming/FEAT-XXX_feature_slug.md`, or a `docs/brainstorming/<feature-slug>/master/` + `phase-NN-<phase-slug>/` folder tree.

- **Single-file shape**: read that one file. Produce one plan for the whole feature (Step 5/Output Rules, single-file branch).
- **Multi-phase folder shape**: read `master/FEAT-XXX_..._master_brainstorming.md` first, then every `phase-NN-<phase-slug>/phase-brainstorming.md` in phase order. Produce one Implementation Plan **per phase** plus one master plan indexing all phases (Step 5/Output Rules, multi-phase branch), mirroring the same phase breakdown — never re-decompose the feature into a different phase split than the brainstorming stage already chose.

Either way, extract the **Feature ID**, **Feature Name**, **MoSCoW Prioritization**, and the **Planning Prompt** section(s).

---

## Step 2 — Read Project Memory
Consult the memory summary and files to check the target codebase design and conventions.

---

## Step 3 — RAG Query
Query `project-rag-search` with the feature name and related keywords.

---

## Step 4 — Targeted Source Inspection (if needed)
Inspect only files explicitly referenced by memory or RAG.

---

## Step 5 — Generate Implementation Plan
Generate the plan document. It must contain the YAML metadata header and the plan sections. Planner MUST directly use the MoSCoW prioritization defined in the brainstorming document to group requirements into implementation phases (e.g., all 'Must' requirements must be placed in Phase 1, 'Should' in Phase 2, etc.) without re-analyzing architecture or scope:

```markdown
<!-- File path (single-file shape):  docs/plans/FEAT-XXX_feature_slug_plan.md -->
<!-- File path (multi-phase shape): docs/plans/<feature-slug>/phase-NN-<phase-slug>/phase-plan.md -->
<!-- File path (multi-phase master): docs/plans/<feature-slug>/master/FEAT-XXX_..._master_plan.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: reviewed
stage: planning
created_at: [YYYY-MM-DD]
updated_at: [YYYY-MM-DD]
previous_artifact: [relative path to the matching brainstorming file/folder — mirror the shape from Step 1]
next_artifact: [relative path to the matching blueprint file/folder once created — see plan-to-blueprint, docs/blueprints/]
---

# FEAT-XXX: [Human Readable Name]

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | [...] | [x] |
| FR-02 | Phase 1 | Task 1.2 | [...] | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Coder] - Triển khai...
- **Task 1.2**: [Architect] - Thiết kế...

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2
- **Parallel Tasks**: [Task 1.3, Task 1.4]
- **Blocking Tasks**: Task 2.1 (blocks Task 2.2)
- **Independent Tasks**: Task 3.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1
  - Group 2: Task 1.3, Task 1.4 (Parallel)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation (Create/Modify/Delete/Do Not Modify) | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/knowledge-runtime/scripts/...` | Create | Tạo cấu trúc gói |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: [...]
- **Provider Pattern details**: [...]
- **Data Flow / Sequence Flow**: [...]
- **Migration Strategy & Testing Architecture**: [...]

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: [...] (Mapped to Task 1.1)
- **Integration Tests**: [...] (Mapped to Task 2.1)
- **Compatibility / Regression Tests**: [...]

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% Unit Tests vượt qua (Pass).
  - [ ] Giao diện API được cài đặt đầy đủ.
- **Phase 2 Exit Criteria**:
  - [ ] Đồ thị liên kết backlinks được cập nhật đúng.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi kiểm thử hệ thống nghiêm trọng không thể khắc phục nhanh.
  - Steps: Revert git commit, khôi phục cấu hình tri thức cũ.
  - Recovery: Trả về trạng thái hoạt động bình thường trên main.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | No | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/blueprints/FEAT-XXX_blueprint.md (or the matching phase-blueprint.md under docs/blueprints/<feature-slug>/)
- **Phase 2 Artifacts**: docs/adr/ADR-XXX.md, docs/releases/Release_Notes.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: [...]
- **Parallel execution opportunities**: [...]
- **Expected token savings**: [...]
- **Recommended execution strategy**: [...]

## Recommended Next Skill
/blueprint
```

---

## Step 6 — Internal Plan Review Gate

Self-review the generated Implementation Plan before handing off to Blueprint.

Review checklist:
- The Plan covers every in-scope FR/NFR/TC from the Brainstorming document.
- Task ownership uses the correct agent responsibilities (Planner, Architect, Coder, QA, QC/Reviewer, Release Manager, and specialists where relevant).
- Task dependencies, roadmap/phasing, parallel groups, rollback, verification strategy, and artifact production plan are internally consistent.
- The Plan stays at planning depth: no classes, functions, API schemas, database schemas, folder structures, or pseudo-code.
- All paths are project-relative and artifact placement follows `AI_RULES.md`.
- `document-compliance-assessment` no-go conditions are not present.
- If the plan touches UI/UX, frontend components, layout, spacing, typography, color, animation, icons, visual hierarchy, aesthetic styling, or design-system decisions, `frontend-design` has been used and its relevant constraints are captured for Blueprint.

Rules:
- Do not stop for user approval at this gate.
- If review FAILS, state the exact failed points and revise only those points.
- Repeat review/revision until PASS.
- Continue to Blueprint handoff only after review passes.

---

# Output Rules

Mirror whichever shape Step 1 detected for this feature:

**Single-file shape** — create exactly two files:
1. `docs/plans/FEAT-XXX_feature_slug_plan.md`
2. `docs/plans/FEAT-XXX_feature_slug_plan.json`

**Multi-phase folder shape** — for each phase, create:
1. `docs/plans/<feature-slug>/phase-NN-<phase-slug>/phase-plan.md`
2. `docs/plans/<feature-slug>/phase-NN-<phase-slug>/phase-plan.json`

Plus one master plan indexing every phase:
1. `docs/plans/<feature-slug>/master/FEAT-XXX_..._master_plan.md`
2. `docs/plans/<feature-slug>/master/FEAT-XXX_..._master_plan.json`

First line of every Markdown file must be its own real path, e.g.:
```html
<!-- File path: docs/plans/FEAT-XXX_feature_slug_plan.md -->
<!-- or: docs/plans/<feature-slug>/phase-NN-<phase-slug>/phase-plan.md -->
```

The JSON file must conform to this schema:
```json
{
  "phases": [
    {
      "phase_name": "Phase 1: ...",
      "tasks": ["Task 1.1", "Task 1.2"],
      "deliverables": ["..."],
      "milestones": ["..."]
    }
  ],
  "tasks": [
    {
      "id": "Task 1.1",
      "description": "...",
      "effort_hours": 4,
      "owner": "Coder",
      "operations": ["NEW", "MODIFY"],
      "files": ["relative/path/to/file"]
    }
  ],
  "dependencies": {
    "Task 1.2": ["Task 1.1"]
  },
  "parallel_groups": [
    ["Task 1.3", "Task 1.4"]
  ],
  "exit_criteria": ["..."],
  "rollback": {
    "trigger": "...",
    "steps": ["..."]
  },
  "tests": [
    {
      "test_target": "relative/path/to/test_file.py",
      "mapped_tasks": ["Task 1.1"]
    }
  ],
  "artifacts": ["docs/blueprints/FEAT-XXX_blueprint.md"]
}
```

---

# Constraints

- Do NOT describe technical implementation.
- Do NOT define classes, functions, or interfaces.
- Do NOT define APIs, database schemas, SQL, or folder structures.
- Do NOT generate pseudo-code.
- Planning must remain understandable by both technical and non-technical stakeholders.
- Keep the plan concise and focused entirely on project management.

---

# IDE Skill Hardening & Boundary Rules

## 1. Single Responsibility
Convert a master brainstorming planning prompt into a formal Implementation Plan and internally review it until PASS. Once the reviewed plan output (single file, or every phase's `phase-plan.md` + master index for the multi-phase shape) is generated under `docs/plans/`, return control to the workflow coordinator. Do not request user approval for this intermediate artifact.

## 2. Never Execute Next Phase
Do NOT directly invoke `plan-to-blueprint` or any other Skill when acting as a worker. In an orchestrated continuous workflow, the workflow-coordinator may route the next phase after this reviewed Plan is complete.

## 3. Workspace Modification Policy
Only create or update the target implementation plan file. No source code changes.

---

## Completion Contract

```text
Current Phase:
Phase 2 — Planning Prompt to Plan

Status:
Completed

Memory Status:
[Fresh | Medium | Low]

Memory Confidence:
[High | Medium | Low]

Memory Documents Read:
[list]

RAG Query:
[query text used]

Source Files Inspected:
[list or "None — answered from memory"]

Generated Output:
[Single-file shape: docs/plans/FEAT-XXX_feature_slug_plan.md (+ .json)]
[Multi-phase shape: docs/plans/<feature-slug>/master/FEAT-XXX_..._master_plan.md (+ .json)
 + docs/plans/<feature-slug>/phase-NN-<phase-slug>/phase-plan.md (+ .json)]

Recommended Next Skill:
plan-to-blueprint

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
