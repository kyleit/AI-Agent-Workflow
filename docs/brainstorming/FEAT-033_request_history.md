<!-- docs/brainstorming/FEAT-033_request_history.md -->

---
feature_id: FEAT-033
feature_name: Request History System
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-033_request_history_plan.md
---

# Master Requirement Document – Request History

## 1. Feature ID & Name
- **Feature ID**: FEAT-033
- **Feature Name**: Request History System

## 2. Original Idea
Implement a **Request History** system that allows users to audit every provider/model request made during an AIWF workflow.

This phase builds on Phase 1 Context Breakdown.

The user must be able to answer:
> Which request consumed the most tokens, cost, time, and tool activity?

---

## 3. Business Problem
- **Problem**: Hiện tại, hệ thống AIWF chỉ lưu trữ lượng token tích lũy ở cấp độ Workflow/Conversation. Ba không thể biết cụ thể từng request LLM đơn lẻ tiêu tốn bao nhiêu tài nguyên (tokens, chi phí, thời gian) và hoạt động của công cụ (tool call count, memory/RAG hits).
- **Why it matters**: Thiếu khả năng quan sát chi tiết dẫn đến khó khăn trong tối ưu hóa prompt, kiểm soát chi phí LLM, và gỡ lỗi khi có request thất bại.
- **Who is affected**: Nhà phát triển và vận hành hệ thống AIWF.
- **Expected outcome**: Ba có thể kiểm tra trực tiếp danh sách yêu cầu trên dòng thời gian (timeline), sắp xếp lọc nhanh các request tốn kém nhất, và xem chi tiết cấu trúc context breakdown của riêng request đó.

---

## 4. Requirement Discovery
- **Functional Requirements**:
  * **FR-01**: Ghi nhận mỗi lượt request LLM chính xác một lần với một ID duy nhất (`request_id`).
  * **FR-02**: Cơ chế khóa và kho khóa duy nhất để tránh trùng lặp dữ liệu khi nạp lại trạng thái.
  * **FR-03**: Hỗ trợ lọc (workflow, project, skill, provider, model, status, time range).
  * **FR-04**: Hỗ trợ sắp xếp (cost, tokens, duration, timestamp, context usage %).
  * **FR-05**: CLI hiển thị danh sách request dưới dạng bảng đọc được và dạng JSON.
  * **FR-06**: Giao diện Visualizer hiển thị Timeline dạng bảng và khung xem chi tiết Request (Metadata, Context Breakdown của request đó, Tool calls, Workspace reads, Memory/RAG usage, Error details).
- **Non-functional Requirements**:
  * **NFR-01**: Tốc độ truy vấn dưới 100ms trên cơ sở dữ liệu có hàng ngàn bản ghi.
  * **NFR-02**: Không tính toán logic request history bên trong Webview.
- **Technical Constraints**:
  * **TC-01**: Lưu trữ dữ liệu trong SQLite (`project_runtime.db`) làm Single Source of Truth.
  * **TC-02**: Bảo toàn các dữ liệu cũ trong cơ sở dữ liệu khi chạy di trú schema (migrations).

---

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần hỗ trợ các cột chỉ mục cụ thể nào cho việc tìm kiếm nhanh không? | Cần đánh chỉ mục cho: `project_id`, `workflow_id`, `conversation_id`, `request_id`, `skill_name`, `provider`, `model`, `created_at`, `total_tokens`, `cost_usd`. |
| Làm thế nào để liên kết một Request với Context Breakdown của Phase 1? | Mỗi request khi được ghi nhận sẽ lưu kèm một khóa ngoại hoặc cấu trúc JSON mô tả Context Breakdown của thời điểm thực hiện request đó. |

---

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (Score >= 85)

---

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Hệ thống lưu trữ SQLite hiện tại đã có bảng `usage_records` ghi nhận lượng token tích lũy của conversation. Bảng mới sẽ được tích hợp song song để lưu lịch sử request chi tiết.

---

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| CLI Runtime Engine | [workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Cần tích hợp lệnh CLI `usage requests` |
| Visualizer extension | [extension.ts](file:///e:/AgentsProject/extensions/visualizer/src/extension.ts) | Nạp dữ liệu từ SQLite sang Webview |

---

## 9. Solution Options Evaluated

### Option A: SQLite Database với bảng `provider_requests` chuyên biệt (Khuyên dùng)
- **Overview**: Thêm bảng mới `provider_requests` trong SQLite `project_runtime.db` với đầy đủ các cột thông tin và chỉ mục hỗ trợ lọc/sắp xếp nhanh.
- **Advantages**: Đảm bảo an toàn dữ liệu, truy vấn hiệu suất cao, đúng chuẩn kiến trúc SQLite của dự án.
- **Disadvantages**: Cần xây dựng logic migration tự động khi mở rộng schema.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Tệp tin JSON Lines lịch sử
- **Overview**: Ghi log nối đuôi vào một tệp tin `.jsonl` trong thư mục `.agents/runtime/`.
- **Advantages**: Cực kỳ dễ triển khai, không cần thực hiện migration cơ sở dữ liệu.
- **Disadvantages**: Hiệu suất thấp khi lọc/sắp xếp trên lượng bản ghi lớn, dễ xung đột ghi tệp tin.

---

## 10. Solution Comparison Table
| Criteria | Option A (SQLite) | Option B (JSON Lines) |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Medium |
| Performance | High | Low |
| Maintainability | High | Low |
| Compatibility | High | Low |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

---

## 11. Selected Solution
- **Choice**: Option A — SQLite Database
- **Why Selected**: Đảm bảo tối đa tính nhất quán dữ liệu, an toàn giao dịch, hiệu suất cao khi khối lượng request tăng lên và phù hợp hoàn toàn với ràng buộc kiến trúc của Ba.

---

## 12. Risks & Assumptions
- **Risks**: Trùng lặp request khi chạy đồng bộ trạng thái nhiều lần.
  - *Mitigation*: Định nghĩa ràng buộc UNIQUE trên khóa `request_id` kết hợp xử lý `INSERT OR IGNORE` để đảm bảo dữ liệu ghi nhận chính xác 1 lần duy nhất.

---

## 13. Acceptance Criteria
- [ ] Mọi request gọi provider LLM được lưu trữ chính xác một lần duy nhất vào SQLite.
- [ ] Hỗ trợ đầy đủ các lệnh CLI truy vấn lọc và sắp xếp theo cost, tokens, duration,...
- [ ] Giao diện Webview có panel Request History hiển thị danh sách dạng Timeline và khung xem chi tiết Request (kèm Context Breakdown tương ứng).
- [ ] Không xảy ra trùng lặp dữ liệu khi đồng bộ hóa lặp lại.

---

## 14. Final Planning Prompt

### Purpose
Tạo prompt tự chứa đầy đủ thông tin cho Skill `brainstorming-to-plan` để thiết lập Bản kế hoạch triển khai.

### Problem Statement
Xây dựng hệ thống quan sát chi tiết (Request History) lưu trữ mọi yêu cầu LLM vào SQLite và cung cấp khả năng phân tích trực quan qua CLI/Visualizer để tìm ra request đắt đỏ nhất, tốn token nhất hoặc bị lỗi.

### Objectives & Selected Solution
- Thiết lập bảng cơ sở dữ liệu `provider_requests` mới trong SQLite.
- Xây dựng CLI `usage requests` hỗ trợ lọc và sắp xếp.
- Bổ sung panel Request History timeline và detail view trên Visualizer Webview.

### Verification Checklist
- [ ] docs/plans/FEAT-033_request_history_plan.md được tạo và phê duyệt.
- [ ] Toàn bộ unit tests kiểm thử logic ghi nhận, lọc, sắp xếp, chống trùng lặp đạt 100% PASS.
