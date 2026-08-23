---
name: workflow-coordinator
description: "The single canonical entry gate of the AIWF framework. Use at the start of every feature, bug fix, or task request to classify intent, verify the Bootstrap Receipt, load workflow state, enforce the documentation sync gate and approval gates, and dispatch to the correct specialist skill (quick-fix, quick-feature, brainstorming, blueprint-to-implementation, debug, verify, git-governance, release-governance). Specialist skills must never be invoked directly from a raw user prompt."
command: tick
aliases:
  - coordinate
  - dispatch
category: workflow
tags:
  - orchestrator
  - workflow
  - runtime
  - stateless
version: 3.16.0
license: MIT
repository: https://gitlab.com/your-org/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-07-29
canonical_entrypoint: true
entrypoint_authority: canonical
wrapper_entrypoint: aiwf
role: canonical_workflow_entrypoint
authority: route_and_delegate
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
accepted_wrapper: aiwf
fail_closed_on_missing_receipt: true
raw_intent_delegation: raw-intent-normalization
requirement_delegation: requirement-specification
brainstorming_delegation: brainstorming
plan_delegation: brainstorming-to-plan
blueprint_delegation: plan-to-blueprint
implementation_delegation: blueprint-to-implementation
debug_delegation: implementation-to-debug
verification_delegation: debug-to-verify
test_governance_delegation: test-execution-governance
git_governance_delegation: git-governance
release_governance_delegation: release-governance
canonical_entrypoint: true
canonical_entrypoint_count: 1
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
artifact_persistence_gate_required: true
artifact_root_pattern: docs/aiwf-runs/<workflow-id>
no_blueprint_no_code: true
documentation_first: true
transactional_doc_source_sync_required: true
documentation_sync_gate_required: true
min_blueprint_readiness_score: 95
code_block_gate_required: true
source_write_guard_required: true
fail_closed_without_bootstrap: true
fail_closed_without_artifact_persistence: true
fail_closed_without_blueprint: true
fail_closed_without_code_block_gate: true
fail_closed_on_stale_documents: true
fail_closed_without_doc_sync_gate: true
---

# Skill: workflow-coordinator (AIWF Canonical Workflow Coordinator)

## 1. Overview & Role
Skill `workflow-coordinator` là Cổng Điều hướng Chính thức (`CANONICAL_ENTRYPOINT`) duy nhất của AIWF framework (`canonical_entrypoint_count = 1`).

> [!CRITICAL]
> **Mandatory Transactional Synchronization & Sync Gate Rules**:
> 1. `NO REQUIRED DOCUMENT = NO CODE` & `NO BLUEPRINT = NO CODE`: Coordinator BẮT BUỘC từ chối điều hướng tới `blueprint-to-implementation` hoặc bất kỳ hành động sửa mã nguồn nào nếu chưa có bộ tài liệu tiền triển khai hoàn chỉnh.
> 2. `DOCUMENTATION_SYNC_GATE` BẮT BUỘC phải đạt `PASS` (`all_required_documents_exist`, `zero_stale_documents`, `zero_missing_documents`, `all_sha256_verify`).
> 3. Nếu bất kỳ tài liệu nào bị `STALE` hoặc `MISSING`, coordinator BẮT BUỘC chặn lệnh `@aiwf next`, `@aiwf continue`, và từ chối phát hành `FEATURE_IMPLEMENTATION_COMPLETED` hay `READY_FOR_DEBUG`.
> 4. CẤM suy luận phê duyệt từ yêu cầu chat của người dùng. Phải có tệp `blueprint-approval-request.json` và `implementation-approval-request.json` hợp lệ.
> 2. Nếu Bootstrap Receipt không hợp lệ (`BOOTSTRAP_RECEIPT_INVALID`), sai lệch project (`BOOTSTRAP_CONTEXT_MISMATCH`), hoặc mã băm SHA-256 không khớp (`HASH_MISMATCH`): Coordinator lập tức từ chối điều hướng và trả về thông báo lỗi rào cản khởi tạo.
> 3. Cấm điều hướng trực tiếp sang Specialist Skills (`quick-fix`, `quick-feature`, `implementation`, `debug`, `verify`, `git-governance`, `release-governance`) nếu chưa qua `initialize-workflow`.

---

## 3. Receipt Verification Checklist
Trước khi nhận lệnh và điều hướng:
- [ ] Receipt tồn tại và đúng định dạng schema `bootstrap-receipt.schema.json`.
- [ ] `bootstrap_skill` = `initialize-workflow`.
- [ ] `decision` = `BOOTSTRAP_READY` hoặc `BOOTSTRAP_READY_READ_ONLY`.
- [ ] `repository_root` trùng khớp với kết quả `git rev-parse --show-top-level`.
- [ ] `project_id` trùng khớp với project active trong `.agents/state`.
- [ ] `content_hash` khớp 100% mã băm SHA-256.
- [ ] Không có `blocking_findings`.
