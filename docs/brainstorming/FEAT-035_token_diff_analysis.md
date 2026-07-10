<!-- docs/brainstorming/FEAT-035_token_diff_analysis.md -->

---
feature_id: FEAT-035
feature_name: Token Diff Analysis
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-035_token_diff_analysis_plan.md
---

# Master Requirement Document – Token Diff Analysis

## 1. Feature ID & Name
- **Feature ID**: FEAT-035
- **Feature Name**: Token Diff Analysis

## 2. Original Idea
[Exact user input, unmodified]
Compare every request against its previous request and calculate:
- Added tokens
- Removed tokens
- Net token change
- Growth percentage
- Largest contributors

Support diffs for:
- Conversation History
- Current Prompt
- AI_RULES
- AGENTS
- SKILL.md
- Brainstorming
- Plans
- Blueprints
- ADRs
- Memory
- RAG
- Workspace Reads
- Tool Results
- Build/Test Logs
- Other runtime context

## 3. Business Problem
- **Problem**: Người dùng chỉ thấy lượng token hoạt động cuối cùng của bước mà không thể lý giải tại sao lượng token đó lại tăng lên hoặc giảm đi (ví dụ: tại sao tăng từ 247K lên 510K).
- **Why it matters**: Khả năng phân tích lý do tăng/giảm token giúp tối ưu chi phí LLM và ngăn ngừa phình to context window vô ích.
- **Who is affected**: Nhà phát triển và chuyên gia tối ưu hóa prompt sử dụng AIWF.
- **Expected outcome**: Hiển thị bảng phân tích chi tiết sự khác biệt lượng token giữa bất kỳ 2 lượt LLM request nào.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: So sánh hai LLM request kế tiếp hoặc ngẫu nhiên từ lịch sử.
  - FR-02: Phân loại sai biệt thành 15 danh mục chuẩn của Phase 1.
  - FR-03: Tính toán lượng token Thêm, Bớt, Thay đổi ròng và Tỷ lệ tăng trưởng.
  - FR-04: Lưu trữ lịch sử diff kế tiếp vào cơ sở dữ liệu SQLite.
  - FR-05: Cung cấp API dòng lệnh (CLI) để truy vấn diff.
  - FR-06: Giao diện Webview hiển thị bảng Token Diff chi tiết kèm đồ thị Waterfall/Delta.
- **Non-functional Requirements**:
  - NFR-01: Phép so sánh và tính toán thực hiện hoàn toàn ở Backend để giữ Single Source of Truth.
  - NFR-02: Độ trễ phản hồi khi tính toán động dưới 100ms.
- **Technical Constraints**:
  - TC-01: Tái sử dụng bảng `provider_requests` và cột `context_breakdown_json` của Phase 2.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần hỗ trợ so sánh 2 request thuộc 2 cuộc hội thoại (conversation) khác nhau không? | Không, chỉ cần so sánh trong cùng một conversation_id. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: SQLite `project_runtime.db` lưu trữ đầy đủ `provider_requests` có chứa context breakdown chi tiết của từng request.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Database Handler | `skills/workflow-runtime/scripts/db.py` | Quản lý bảng lưu trữ và truy vấn dữ liệu |
| Context Analyzer | `skills/workflow-runtime/scripts/context.py` | Trích xuất và phân tích transcript log |
| Visualizer Webview | `extensions/visualizer/resources/webview.html` | Hiển thị bảng điều khiển Token Diff |

## 9. Solution Options Evaluated

### Option A: Python Diff Engine + SQLite consecutive diff table (Khuyên dùng)
- **Overview**: Lưu trữ các diff liền kề vào bảng `token_diffs` để truy xuất nhanh; đồng thời cho phép gọi CLI để tính toán động diff của 2 request ngẫu nhiên khi người dùng lựa chọn từ timeline.
- **Advantages**: Cân bằng tối ưu giữa hiệu năng truy vấn nhanh và tính linh hoạt cao.
- **Disadvantages**: Cần viết thêm module xử lý diff toán học ở Python.
- **Complexity**: Medium
- **Risk**: Low
- **Performance**: High
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Tính toán động hoàn toàn ở Frontend Webview
- **Overview**: Webview nhận danh sách breakdown và tự tính toán hiệu số bằng Javascript.
- **Disadvantages**: Vi phạm nguyên tắc Single Source of Truth, khó viết test case tự động xác thực ở Backend.
- **Complexity**: Medium
- **Risk**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | Medium |
| Risk | Low | Medium |
| Performance | High | High |
| Maintainability | High | Low |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 11. Selected Solution
- **Choice**: Option A — Python Diff Engine + SQLite consecutive diff table
- **Why Selected**: Đảm bảo chuẩn hóa toán học tập trung tại Backend, dễ viết unittest, hoạt động nhất quán giữa cả giao diện Webview và CLI dòng lệnh.

## 12. Risks & Assumptions
- **Risks**: Trùng lặp khóa hoặc không tìm thấy request kế tiếp khi có lỗi sync.
  - **Mitigation**: Sử dụng mã lỗi an toàn và mặc định diff = 0 nếu không tìm thấy request trước đó.

## 13. Acceptance Criteria
- [ ] Tính toán chính xác sai số (+/-) và tỷ lệ thay đổi từng danh mục.
- [ ] Dữ liệu hiển thị đồng bộ giữa CLI và Webview.

---

## 14. Final Planning Prompt

### Purpose
Bàn giao thông tin đầy đủ cho Planning Agent thực hiện thiết kế chi tiết cho Phase 3.

### Problem Statement
Nhà phát triển cần hiểu rõ nguyên nhân tăng trưởng kích thước Context Window giữa các model request của AIWF workflow để tối ưu hóa chi phí.

### Objectives & Selected Solution
Xây dựng công cụ so sánh Token Diff ở backend Python, lưu lịch sử liền kề vào bảng `token_diffs` và tích hợp bảng so sánh động lên giao diện Webview.

### Verification Checklist
- [ ] docs/plans/FEAT-035_token_diff_analysis_plan.md được phê duyệt.
- [ ] docs/designs/FEAT-035_token_diff_analysis_blueprint.md được phê duyệt.
- [ ] Tất cả các test case trong `test_diff_engine.py` đều PASS.
