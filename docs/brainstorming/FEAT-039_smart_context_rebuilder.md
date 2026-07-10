<!-- docs/brainstorming/FEAT-039_smart_context_rebuilder.md -->

---
feature_id: FEAT-039
feature_name: Smart Context Rebuilder
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-039_smart_context_rebuilder_plan.md
---

# Master Requirement Document – Smart Context Rebuilder

## 1. Feature ID & Name
- **Feature ID**: FEAT-039
- **Feature Name**: Smart Context Rebuilder

## 2. Original Idea
[Exact user input, unmodified]
Eliminate unnecessary provider input by rebuilding only the minimum context required for each request.
Instead of replaying the entire conversation history, dynamically construct an optimized context bundle.

Core Principles:
The Smart Context Rebuilder must become the single context assembly layer before every provider request.
It must never blindly reuse the complete chat history.
Context should be assembled from:
- Current task
- Active workflow state
- Relevant Blueprint sections
- Relevant Plan sections
- Relevant Brainstorming sections
- Project Memory
- RAG results
- Changed files only
- Runtime summaries
- Cached symbol information
- Explicit user instructions

Context Assembly Engine:
Implement a Context Assembly Engine capable of:
1. Identifying required context.
2. Removing duplicated information.
3. Replacing repeated documents with summaries.
4. Using hash-based cache validation.
5. Loading only changed artifacts.
6. Producing a deterministic Context Bundle.
Every bundle must include diagnostics:
- Bundle size
- Estimated tokens
- Sources included
- Sources skipped
- Estimated savings

Runtime Cache:
Implement cache layers for:
- Blueprint summaries
- AI_RULES summaries
- Skill metadata
- Workspace symbols
- Memory lookups
- RAG lookups
Invalidate cache only when source hashes change.

Dashboard:
Create a Smart Context Rebuilder page showing:
- Context Bundle
- Included sources
- Skipped sources
- Cache hits
- Cache misses
- Estimated token savings
- Before vs After bundle size

CLI:
Add commands equivalent to:
- context bundle
- context preview
- context rebuild
- context cache
- context explain
Adapt naming to the existing AIWF CLI.

Database:
Persist:
- Context bundles
- Cache metadata
- Source hashes
- Rebuild history
- Estimated savings
Maintain backward compatibility.

Automated Tests:
Verify:
- No duplicate context
- Cache invalidation
- Hash changes
- Bundle determinism
- Reduced provider input
- Resume workflow compatibility
- Multi-project isolation

Success Criteria:
Target measurable improvements:
- Reduce accumulated provider input by 80–95% on long-running workflows.
- Preserve answer quality.
- Never omit required context.

## 3. Business Problem
- **Problem**: Việc gửi lại toàn bộ hội thoại cũ làm phình to tokens đầu vào (input tokens) theo lũy thừa, làm tăng chi phí LLM đột biến và lãng phí thời gian xử lý của nhà cung cấp API.
- **Why it matters**: Tiết kiệm chi phí đầu vào lên tới 95%, đảm bảo agent hoạt động lâu dài không bị tràn giới hạn tokens (2.0M tokens).
- **Who is affected**: Lập trình viên và toàn bộ hệ thống đại lý tự động chạy dài hạn.
- **Expected outcome**: Bộ xây dựng ngữ cảnh động thông minh (Context Assembly Engine) làm tầng tập hợp ngữ cảnh duy nhất.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Bộ lắp ráp Context Assembly Engine gộp ngữ cảnh từ 11 nguồn tài nguyên chính.
  - FR-02: Bộ cache dựa trên Hash (SHA256) lưu trữ tóm tắt Blueprint, AI_RULES, Symbols.
  - FR-03: Ghi nhận lịch sử rebuild, mã băm nguồn và lượng tokens tiết kiệm vào SQLite.
  - FR-04: CLI tích hợp các subcommands `usage context` và giao diện Webview Dashboard Tab hiển thị nguồn Include/Skip và so sánh dung lượng.
- **Non-functional Requirements**:
  - NFR-01: Quá trình tính mã băm tệp và ráp ngữ cảnh phải chạy song song, dưới 100ms.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm sao đảm bảo chất lượng phản hồi của LLM khi rút gọn ngữ cảnh cũ? | Engine sẽ luôn ưu tiên nạp: Trạng thái task hiện tại, rules cốt lõi, Project Memory đã tóm tắt và chỉ những tệp có sự thay đổi (diff) thực tế trong Git. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Solution Options Evaluated

### Option A: Context Assembly Engine + Hash-based Cache + Dashboard Tab (Khuyên dùng)
- **Overview**:
  - Viết module `context_rebuilder.py` để ráp Context Bundle.
  - SQLite lưu trữ cấu hình cache (`cache_metadata`) và lịch sử ráp (`rebuild_history`).
  - CLI mở rộng các subcommands `usage context preview`, `usage context cache`.
  - Tab quản trị trực quan trên Webview Dashboard.
- **Advantages**: Cắt giảm token đầu vào triệt để và an toàn, tận dụng tốt Project Memory.
- **Complexity**: High
- **Risk**: Low

### Option B: Chỉ tóm tắt lịch sử chat đơn thuần dựa trên số lượng request gần nhất
- **Disadvantages**: Mất đi các tệp thông tin ngữ cảnh quan trọng, không có cache mã băm an toàn.

## 8. Selected Solution
- **Choice**: Option A — Context Assembly Engine + Hash-based Cache + Dashboard Tab

## 9. Acceptance Criteria
- [ ] Giảm tối thiểu 80% input tokens trên các workflow chạy thử dài hạn.
- [ ] Không bỏ sót các rule quan trọng (AI_RULES) và tệp tin đang sửa đổi.
- [ ] Cache tự động bị hủy (invalidate) ngay khi mã băm SHA256 của tệp nguồn thay đổi.
