<!-- docs/brainstorming/FEAT-032_context_breakdown.md -->

---
feature_id: FEAT-032
feature_name: Phase 1 - Context Breakdown
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-032_context_breakdown_plan.md
---

# Master Requirement Document – Phase 1 - Context Breakdown

## 1. Feature ID & Name
- **Feature ID**: FEAT-032
- **Feature Name**: Phase 1 - Context Breakdown

## 2. Original Idea
```text
Implement a Context Breakdown Engine that explains exactly where the current active context is being consumed.
This feature is the foundation for all future runtime optimization work.
Objectives:
Build a runtime service that calculates the token contribution of each context source.
Supported sources include:
- Conversation History
- Current User Prompt
- AI_RULES
- AGENTS
- Loaded SKILL.md files
- Brainstorming documents
- Plans
- Blueprints
- ADRs
- Project Memory
- RAG results
- Workspace file reads
- Tool results
- Build/Test logs
- Other runtime context

Every source must report:
- Estimated Tokens
- Percentage of Active Context
- Number of Loads
- Last Loaded Time
```

## 3. Business Problem
- **Problem**: Hiện tại người dùng chỉ nhìn thấy tổng quan phần trăm dung lượng context đã dùng và còn lại dưới dạng số liệu thô. Thiếu thông tin chi tiết giải thích thành phần nào đang tiêu tốn nhiều token nhất (Ví dụ: do AI_RULES, do SKILL, hay do file đọc trong workspace).
- **Why it matters**: Nếu không có cơ chế breakdown, người dùng và các AI Agents sẽ không thể thực hiện các bước tối ưu hóa thông minh (như xóa bớt tệp tin đọc trùng lặp, cắt ngắn lịch sử hoặc nén prompt).
- **Who is affected**: AI Agent Coder, Reviewer, nhà phát triển (Ba), và chi phí API sử dụng mô hình.
- **Expected outcome**: Một panel trực quan hiển thị dạng cây (Tree view) phân tách chi tiết phần trăm tiêu thụ của từng danh mục tài nguyên context cùng cờ diagnostics dòng lệnh.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01 (Inspect Active Context)**: Bộ phân tích phải đọc tệp log transcript (`transcript.jsonl`) để trích xuất lượt gửi prompt cuối cùng của mô hình.
  - **FR-02 (Classify Context Fragments)**: Phân loại từng phân đoạn context dựa trên các thẻ XML cứu cánh đặc trưng (như `<RULE>`, `<knowledge_items>`, v.v.) hoặc tiêu đề file.
  - **FR-03 (Estimate Tokens)**: Ước lượng số lượng token đóng góp (dựa trên chiều dài ký tự chia 3).
  - **FR-04 (Track Resource Metadata)**: Đếm số lượng tải (Loads count) và thời gian tải cuối cùng (Last Loaded Time) của từng tài nguyên được đọc (ví dụ qua `view_file` trong log).
  - **FR-05 (Structured State Output)**: Lưu kết quả phân tích vào `.agents/state/breakdown.json` dạng split-state.
  - **FR-06 (Diagnostics Command)**: Hỗ trợ lệnh CLI `aiwf usage breakdown` in ra bảng phân tích chi tiết.
  - **FR-07 (Dashboard Tree View)**: Sidebar panel hiển thị Tree view, thanh đo % trực quan, tô đậm nguồn chiếm dung lượng lớn nhất và cho phép thu gọn/mở rộng.
- **Non-functional Requirements**:
  - **NFR-01 (Performance)**: Phép phân tích transcript chạy trong dưới 500ms.
  - **NFR-02 (UX)**: Giao diện trực quan, đồng bộ màu sắc với thiết kế hiện tại của Visualizer.
- **Technical Constraints**:
  - **TC-01 (Pure Split State)**: Lưu kết quả độc lập trong `.agents/state/breakdown.json`.
  - **TC-02 (No External Imports)**: Không sử dụng thư viện ngoài dự án.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm sao phân biệt chính xác nguồn dữ liệu là RAG hay Project Memory? | Dựa vào các thẻ XML đặc thù nạp vào prompt (ví dụ: `<knowledge_items>` cho RAG, `<memory_state>` cho Project Memory) và log lệnh tool_calls của Skills. |
| Nếu tổng phần trăm không khớp chính xác 100% thì sao? | Cần thiết lập một mục "Other" để bù trừ sai số ước lượng ký tự của các phần đệm prompt, đảm bảo tổng xấp xỉ 100%. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](../memory/project-summary.md)
- **Existing Architecture Summary**: Cấu trúc Split State trong `.agents/state/` lưu trữ các tệp trạng thái độc lập (`context.json`, `usage.json`...). Visualizer Extension dùng file watcher để lắng nghe cập nhật và vẽ lại UI.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| context.py | [.agents/skills/workflow-runtime/scripts/context.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/context.py) | Chứa các hàm phân tích transcript và ước lượng token. |
| webview.html | [extensions/visualizer/resources/webview.html](file:///e:/AgentsProject/extensions/visualizer/resources/webview.html) | Nơi xây dựng panel giao diện Breakdown mới. |

## 9. Solution Options Evaluated

### Option A: Static Parser (Phân tích Transcript tĩnh)
- **Overview**: Sử dụng biểu thức chính quy (regex) để quét tệp `transcript.jsonl` lượt cuối cùng, bóc tách các khối văn bản theo thẻ tag XML đặc thù và tính toán dung lượng.
- **Architecture**: Viết `breakdown_engine.py` thực hiện quét transcript và ghi `.agents/state/breakdown.json`.
- **Advantages**: Rất nhanh, an toàn, không can thiệp vào các Skill khác.
- **Disadvantages**: Cần duy trì danh sách thẻ XML chính xác.
- **Complexity**: Low | **Risk**: Low

### Option B: Dynamic Tracker (Theo dõi động)
- **Overview**: Các AI Skills tự động ghi lại siêu dữ liệu mỗi khi nạp file vào một DB trung gian.
- **Advantages**: Cực kỳ chính xác về thời gian load.
- **Disadvantages**: Phải can thiệp sửa đổi quá nhiều file Skills làm tăng nguy cơ lỗi hồi quy.
- **Complexity**: High | **Risk**: High

## 10. Solution Comparison Table
| Criteria | Option A (Static Parser) | Option B (Dynamic Tracker) |
|---|---|---|
| Complexity | Low | High |
| Risk | Low | High |
| Performance | Very High | Medium |
| Maintainability | Medium | Low |
| Compatibility | High | Medium |
| Future Scalability | Medium | High |
| Development Cost | Low | High |

## 11. Selected Solution
- **Choice**: Option A — Static Parser
- **Why Selected**: Đảm bảo an toàn tuyệt đối cho hệ thống lõi, thực thi nhanh dưới 300ms, dễ dàng bảo trì và tích hợp trực tiếp vào tệp Split State hiện tại.

## 12. Risks & Assumptions
- **Risks**: Transcript quá lớn gây chậm khi parse. -> *Mitigation*: Chỉ đọc lượt tương tác cuối cùng của transcript thay vì duyệt từ đầu.

## 13. Acceptance Criteria
- [ ] Xây dựng module `breakdown_engine.py` phân tích chính xác token đóng góp của từng nguồn.
- [ ] Kết quả được lưu tại `.agents/state/breakdown.json`.
- [ ] CLI command `aiwf usage breakdown` hoạt động hiển thị bảng phân tích.
- [ ] Giao diện Visualizer hiển thị Tree view trực quan với progress bar cho từng thành phần.
- [ ] Tỷ lệ phần trăm tổng cộng đạt xấp xỉ 100%.

---

## 14. Final Planning Prompt

### Purpose
Lời gọi hoàn chỉnh và tự chứa thông tin dành cho Skill `brainstorming-to-plan` để lập kế hoạch chi tiết cho FEAT-032.

### Problem Statement
Xây dựng Context Breakdown Engine nhằm bóc tách và giải thích chính xác tỷ lệ tiêu dùng context token của các tài nguyên hệ thống (Luật, Lịch sử, Tệp dự án, RAG...) để làm nền tảng cho việc tối ưu hóa.

### Verification Checklist
- [ ] docs/plans/FEAT-032_context_breakdown_plan.md được sinh và phê duyệt.
- [ ] docs/designs/FEAT-032_context_breakdown_blueprint.md được sinh và phê duyệt.
- [ ] Tích hợp thành công Tree view panel vào visualizer sidebar.
- [ ] Vượt qua toàn bộ unit test tự động.
