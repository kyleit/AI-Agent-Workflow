<!-- docs/brainstorming/FEAT-036_runtime_insights_advisor.md -->

---
feature_id: FEAT-036
feature_name: Runtime Insights & Optimization Advisor
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-036_runtime_insights_advisor_plan.md
---

# Master Requirement Document – Runtime Insights & Optimization Advisor

## 1. Feature ID & Name
- **Feature ID**: FEAT-036
- **Feature Name**: Runtime Insights & Optimization Advisor

## 2. Original Idea
[Exact user input, unmodified]
Transform collected runtime metrics into actionable recommendations.
Instead of only showing numbers, AIWF should explain:
- Why context is growing
- Which artifacts are expensive
- Which skills consume the most tokens
- Which files are repeatedly loaded
- How to reduce future cost

Analytics:
- Top context contributors
- Fastest growing categories
- Repeatedly loaded documents
- Most expensive skills
- Average tokens per request
- Average cost per request
- Context growth trend
- Requests before context reset
- Estimated remaining context

Optimization Engine:
- Move document into Project Memory
- Convert repeated workspace reads into RAG
- Split oversized Blueprint
- Archive old Brainstorming documents
- Reduce Conversation History
- Cache repeated Tool Results
- Replace repeated file reads with runtime cache

Each recommendation must include:
- Expected token savings
- Expected cost reduction
- Priority (High/Medium/Low)
- Confidence score

Dashboard:
- Efficiency score
- Cost trend
- Context trend
- Recommendation cards
- Optimization opportunities
- Estimated savings

CLI:
- insights
- optimize
- recommendations
- efficiency

Database:
- Insight snapshots
- Recommendation history
- Optimization acceptance state

Automated Tests:
- Correct recommendation generation
- Stable efficiency scoring
- Accurate savings estimation
- Dashboard rendering
- SQLite persistence

## 3. Business Problem
- **Problem**: Người dùng có rất nhiều dữ liệu thô (breakdown, requests, diffs) nhưng thiếu sự phân tích tổng hợp thông minh để hiểu tại sao chi phí tăng cao và làm sao để tối ưu hóa.
- **Why it matters**: Tiết kiệm chi phí LLM trực tiếp, giữ context window gọn gàng, tăng tốc độ xử lý của AI.
- **Who is affected**: Tất cả lập trình viên sử dụng hệ thống AIWF.
- **Expected outcome**: Cung cấp đề xuất tối ưu hóa cụ thể bằng số liệu tài chính rõ ràng.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Tính toán các chỉ số phân tích chuyên sâu (Efficiency Score, Avg cost, Avg tokens...).
  - FR-02: Bộ lọc heuristic tự động đề xuất 7 loại tối ưu hóa (Memory, RAG, Blueprint split, Archive, Cache...).
  - FR-03: Đi kèm với mỗi đề xuất: lượng token tiết kiệm, số tiền tiết kiệm ($ USD), độ ưu tiên (High/Med/Low) và điểm tin cậy.
  - FR-04: Lưu trữ snapshot phân tích và lịch sử đề xuất tối ưu (Accept/Ignore/Pending) vào SQLite.
  - FR-05: Giao diện dashboard Runtime Insights sang xịn mịn (Đồ thị xu hướng, thẻ đề xuất hành động).
  - FR-06: CLI dòng lệnh hỗ trợ xem chỉ số và chấp nhận tối ưu.
- **Non-functional Requirements**:
  - NFR-01: Bộ Heuristic Engine chạy độc lập ở Backend Python.
  - NFR-02: Điểm hiệu năng (Efficiency Score) ổn định, không nhảy loạn.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Việc "Accept" một đề xuất có tự động thực hiện hành động (ví dụ: tự động dọn dẹp file) không? | Trong phase này, "Accept" chỉ đánh dấu trạng thái đã chấp nhận trong SQLite để lưu lịch sử tối ưu hóa và cập nhật lại dự toán tiết kiệm. Việc dọn dẹp thực tế vẫn do người dùng hoặc agent thực thi thủ công. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: Bảng `provider_requests` và `token_diffs` đã có sẵn dữ liệu token breakdown của tất cả các request.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Database Handler | `skills/workflow-runtime/scripts/db.py` | Quản lý bảng cơ sở dữ liệu |
| Visualizer Webview | `extensions/visualizer/resources/webview.html` | Hiển thị giao diện Dashboard |

## 9. Solution Options Evaluated

### Option A: Python Analytics Engine + SQLite Persistence + Dashboard Page (Khuyên dùng)
- **Overview**: Tạo module `insights_engine.py` tính toán các chỉ số và đề xuất, lưu trữ snapshot và trạng thái tối ưu hóa vào các bảng SQLite mới (`insight_snapshots`, `recommendations`). Dashboard Webview sẽ gọi CLI để nhận dữ liệu phân tích này.
- **Advantages**: Cấu trúc chặt chẽ, dễ viết unittest, đảm bảo Single Source of Truth tuyệt đối ở backend.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Thực hiện logic tính toán heuristic trực tiếp trên Javascript của Webview
- **Overview**: Webview tự phân tích JSON lịch sử để hiển thị các đề xuất tối ưu.
- **Disadvantages**: Không có persistence lưu lại lịch sử đề xuất (Accept/Ignore), không thể kiểm thử Backend, khó đồng bộ hóa với CLI.
- **Complexity**: High
- **Risk**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | High |
| Risk | Low | Medium |
| Performance | High | Medium |
| Maintainability | High | Low |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 11. Selected Solution
- **Choice**: Option A — Python Analytics Engine + SQLite Persistence + Dashboard Page
- **Why Selected**: Đảm bảo phân tích dữ liệu tập trung ở Backend, hỗ trợ lưu trữ trạng thái chấp nhận tối ưu hóa lâu dài và có độ tin cậy kiểm thử cao nhất.

## 12. Risks & Assumptions
- **Risks**: Thuật toán tính toán điểm hiệu năng hoặc lượng token tiết kiệm dự toán bị sai lệch lớn so với thực tế.
  - **Mitigation**: Đặt các công thức toán học tuyến tính đơn giản dựa trên kích thước thực tế của tài liệu và hệ số nhân chi phí.

## 13. Acceptance Criteria
- [ ] Tính toán đúng Efficiency Score, xu hướng tăng trưởng và dự toán tiết kiệm.
- [ ] Lưu và lấy chính xác trạng thái Accept/Ignore của đề xuất trong SQLite.
- [ ] Giao diện Dashboard hiển thị đầy đủ thẻ đề xuất và đồ thị Insights.

---

## 14. Final Planning Prompt

### Purpose
Bàn giao thông tin đầy đủ cho Planning Agent thực hiện thiết kế chi tiết cho Phase 4.

### Problem Statement
Người dùng cần một bộ cố vấn thông minh (Optimization Advisor) để phân tích chi phí và đề xuất các hành động tối ưu hóa cụ thể dựa trên lịch sử runtime context của AIWF.

### Objectives & Selected Solution
Xây dựng Insights Engine bằng Python kết hợp lưu trữ cơ sở dữ liệu SQLite và tích hợp trang Dashboard chuyên sâu lên visualizer extension.

### Verification Checklist
- [ ] docs/plans/FEAT-036_runtime_insights_advisor_plan.md được phê duyệt.
- [ ] docs/designs/FEAT-036_runtime_insights_advisor_blueprint.md được phê duyệt.
- [ ] Chạy bộ unittest `test_insights_engine.py` đạt PASS 100%.
