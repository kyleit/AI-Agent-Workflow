---
name: orchestrator [DEPRECATED]
command: orchestrate
aliases:
  - orchestrator
  - orchestrate
  - dispatch
category: orchestration
tags:
  - orchestrator
  - workflow
  - runtime
version: 1.0.0
license: MIT
created_at: 2026-07-15
updated_at: 2026-07-15
description: (DEPRECATED) Legacy autonomous execution orchestrator. Use workflow-coordinator instead.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached---

# Skill: orchestrator [DEPRECATED]

> [!WARNING]
> This skill is **DEPRECATED**. Please use the new `workflow-coordinator` skill instead.
> Legacy commands `orchestrator` and `orchestrate` are shimmed and routed internally to `workflow-coordinator`.

---

## Purpose

(DEPRECATED) Legacy autonomous execution orchestrator. Use workflow-coordinator instead.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill interfaces with the aiwf Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint**: Run `aiwf validate --checkpoint "optional"` before taking any action.
- **Progress Tracking**: Update status and log progress using `workflow_runtime.py` when integrated in a workflow session.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill strictly adheres to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.

---

## Overview
The Orchestrator is the single entry point for all framework workflows. It automatically analyzes user intent, builds the execution DAG, handles file locking, runs tasks sequentially, and manages runtime updates, rendering manual skill selection obsolete.

## Orchestrator Responsibilities
1. Only Orchestrator may dispatch agents.
2. Every execution must begin inside Orchestrator.
3. Workers (other Skills) cannot invoke other workers.
4. Workers cannot schedule parallel work, merge outputs, or own workflow state.
5. Only Orchestrator owns workflow, sequential scheduling, dependency graph, merge, conflict resolution, integration, and verification.
6. Workers only execute assigned tasks with restricted write scopes.

## Entry Flow
1. **Load Context**: Load `AI_RULES.md`, `AGENTS.md`, `MANIFEST.json`, `project-profile.json`, memory, RAG, and current session.
2. **Active Workflow Continuation Check**:
   * Before classifying any user request, check the session file (`.agents/.session.json`) for an existing `active_workflow`.
   * If `active_workflow` has `waiting_for` set, and the user's prompt is a continue phrase (e.g., "continue", "tiếp", "tiếp đi", "proceed", "go"):
     * Immediately bypass reclassification.
     * Run the CLI to resume the active workflow:
       ```bash
       aiwf active-workflow resume
       ```
     * Immediately transfer control and execute the instructions of the resumed skill.
     * Stop processing.
3. **Intent Detection & Classification**:
   * If no active workflow is continuation-resumed, classify the user request according to the rules in `software-development-workflow`'s classification matrix.
   * Call `workflow_runtime.py suggest` to persist routing decisions.
   * **Workflow Skill Auto-Dispatch**: If the detected skill is `quick-fix`, `quick-feature`, or `brainstorming`, the Orchestrator MUST immediately transfer execution control to that skill. The Agent must then strictly execute following the specific phases of the target skill (e.g. Specification -> Blueprint -> Implementation for quick-fix/quick-feature), and NEVER bypass any specification or blueprint steps to write source code directly.
   * Present single or ambiguous option layouts, wait for user confirmation via choice protocol, and dispatch to the selected skill via `workflow_runtime.py start`.
4. **Sequential Dispatch & Execution (Implementation Phase Only)**:
   * For all phases, execution runs strictly sequentially.
   * When entering Phase 6 (Implementation / Execute) after blueprint approval (checkpoint >= 5), the Orchestrator executes all tasks sequentially in topological DAG order.
   * Stiffly enforces lock integrity throughout the step-by-step progress.

## 🔒 Blueprint Enforcement & IDE Integration Guide
1. **Quy tắc phối hợp giữa Antigravity IDE và Framework**:
   - Tệp `implementation_plan.md` (yêu cầu của Antigravity IDE) chỉ đóng vai trò là "cầu nối phê duyệt" với IDE để xin phép sửa đổi file.
   - Nội dung của `implementation_plan.md` phải tuân thủ và khớp 100% với tệp Design Blueprint trong thư mục semantic feature tương ứng (ví dụ `docs/features/<feature-family>/blueprints/FEAT-XXX_slug_blueprint.md` hoặc `docs/features/<feature-family>/blueprints/FIX-XXX_slug_blueprint.md`) trong dự án.
   - Agent không được tự biên tự diễn giải pháp mới trong `implementation_plan.md` nếu chưa có Design Blueprint được đăng ký và phê duyệt hợp lệ qua CLI (`aiwf blueprint --approve`).
2. **Chặn cứng Phase 6 (Implementation)**:
   - Nếu session có checkpoint < 5 (chưa phê duyệt Blueprint) và yêu cầu thuộc về một active feature/fix đang triển khai, Orchestrator cấm tuyệt đối đề xuất chạy Implementation. Phải hướng dẫn người dùng chạy Spec/Blueprint phase trước.

## Execution Behavior
- **Sequential Execution**: Run tasks sequentially in topological DAG order. Lock blocks any overlapping concurrent updates to ensure state integrity.
- **Cancel**: Abort execution immediately. Modifies no workspace files.

## Post-Modification Check
- Sau khi bất kỳ Skill nào trong framework được tạo mới hoặc chỉnh sửa, Orchestrator PHẢI khuyến nghị người dùng chạy lệnh xác thực chất lượng Skill để đảm bảo không vi phạm các chính sách an toàn:
  ```bash
  /verify-skill <skill-name>
  ```
