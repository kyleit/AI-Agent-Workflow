<!-- docs/brainstorming/FEAT-038_context_budget_controller.md -->

---
feature_id: FEAT-038
feature_name: Context Budget Controller
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-038_context_budget_controller_plan.md
---

# Master Requirement Document – Context Budget Controller

## 1. Feature ID & Name
- **Feature ID**: FEAT-038
- **Feature Name**: Context Budget Controller

## 2. Original Idea
[Exact user input, unmodified]
Transform AIWF from a passive monitoring system into an active runtime controller that prevents unnecessary context growth before it happens.
The controller proactively enforces configurable context budgets.

Core Responsibilities:
Implement a Context Budget Controller capable of:
- Predicting context growth before every provider request.
- Evaluating whether the request exceeds the configured budget.
- Selecting the best optimization strategy automatically.
- Explaining every decision.
- Recording all optimization actions.

Budget Policies:
Support configurable policies:
- Soft Warning
- High Usage
- Critical Usage
- Emergency Protection
Default thresholds should be percentage-based and configurable.
Support different policies per provider/model.

Optimization Strategies:
The controller may recommend or execute (depending on configuration):
- Compress conversation history
- Replace history with workflow summary
- Reload from Project Memory
- Reload from RAG
- Remove duplicated tool results
- Remove duplicated workspace reads
- Replace repeated blueprint loading with cached summary
- Split workflow into a new session
- Spawn a sub-agent for isolated work
- Create a Resume Workflow checkpoint

Every action must estimate:
- Tokens saved
- Cost saved
- Confidence
- Side effects

Runtime Decision Engine:
Before every provider request:
1. Calculate predicted context.
2. Compare against budget.
3. Rank optimization strategies.
4. Apply or recommend the safest strategy.
5. Log the decision.
Never perform destructive optimization without explicit policy support.

Dashboard:
Create a dedicated Context Budget Controller page.
Display:
- Current budget
- Predicted usage
- Remaining budget
- Recommended action
- Optimization history
- Estimated savings
- Budget policy
- Auto/Manual mode

CLI:
Provide commands equivalent to:
- budget status
- budget simulate
- budget optimize
- budget policies
- budget history
Adapt naming to the existing AIWF CLI.

Database:
Persist:
- Budget snapshots
- Optimization decisions
- Applied strategies
- Estimated savings
- Policy configuration
Maintain backward compatibility.

Automated Tests:
Verify:
- Healthy workflow
- Near-budget workflow
- Budget exceeded
- Automatic recommendation
- Manual approval flow
- Resume workflow suggestion
- Multi-provider policies
- Duplicate optimization prevention

## 3. Business Problem
- **Problem**: Context phình to quá nhanh gây lãng phí chi phí API LLM và tăng nguy cơ tràn ngữ cảnh khiến agent thất bại giữa chừng.
- **Why it matters**: Kiểm soát chủ động chi phí và dung lượng trước khi gửi request API giúp AIWF tiết kiệm tài nguyên tốt hơn 50%.
- **Who is affected**: Lập trình viên và các kiến trúc sư AI vận hành workflow dài hạn.
- **Expected outcome**: Bộ điều khiển chủ động ngân sách thông qua CLI và Dashboard.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Định nghĩa 4 chính sách ngân sách (Soft Warning, High, Critical, Emergency).
  - FR-02: Bộ máy phân tích quyết định (Decision Engine) xếp hạng và đề xuất 10 chiến lược tối ưu hóa.
  - FR-03: Lưu trữ lịch sử áp dụng tối ưu hóa và snapshot ngân sách vào SQLite.
  - FR-04: Thiết kế tab quản trị ngân sách chuyên dụng trên Webview và CLI subcommands `usage budget`.
- **Non-functional Requirements**:
  - NFR-01: Tốc độ kiểm định ngân sách trước mỗi request phải dưới 50ms.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Chế độ Auto vs Manual tối ưu hóa hoạt động thế nào? | Trong chế độ Auto, các hành động tối ưu hóa an toàn (như dọn dẹp file trùng) sẽ được thực thi trực tiếp, còn các hành động thay đổi cấu trúc lớn (như nén lịch sử) sẽ được đề xuất qua Webview để người dùng phê duyệt (Manual). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Solution Options Evaluated

### Option A: Active Decision Engine + SQLite Config + Dashboard Tab (Khuyên dùng)
- **Overview**:
  - Phát triển module `budget_controller.py` hoạt động trước mỗi request.
  - Tạo bảng di trú SQLite `budget_policies`, `budget_history`.
  - CLI hỗ trợ thêm lệnh `usage budget status`, `usage budget optimize`, `usage budget history`.
  - Tab quản trị trực quan trên Webview Dashboard.
- **Advantages**: Chủ động can thiệp hiệu quả trước LLM request, thống kê tiết kiệm tài nguyên chuẩn xác.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Báo cáo thụ động trên Webview sau khi LLM request đã hoàn tất
- **Disadvantages**: Không thể chặn và tối ưu hóa trước khi lãng phí token xảy ra.

## 8. Selected Solution
- **Choice**: Option A — Active Decision Engine + SQLite Config + Dashboard Tab

## 9. Acceptance Criteria
- [ ] Chặn request thành công khi vượt ngưỡng Emergency Protection.
- [ ] Tính toán đúng số lượng tokens và chi phí tiết kiệm dự phòng.
- [ ] Giao diện hiển thị đúng chế độ Auto/Manual và lịch sử áp dụng.
