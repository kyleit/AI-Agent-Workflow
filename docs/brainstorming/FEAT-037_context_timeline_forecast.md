<!-- docs/brainstorming/FEAT-037_context_timeline_forecast.md -->

---
feature_id: FEAT-037
feature_name: Context Timeline & Predictive Analytics
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-037_context_timeline_forecast_plan.md
---

# Master Requirement Document – Context Timeline & Predictive Analytics

## 1. Feature ID & Name
- **Feature ID**: FEAT-037
- **Feature Name**: Context Timeline & Predictive Analytics

## 2. Original Idea
[Exact user input, unmodified]
Build a visual timeline that explains how context, tokens, cost, and runtime behavior evolve throughout an entire workflow.
The system must not only display history but also predict future context growth.

Objectives:
Create a Timeline Engine that records every significant workflow event.
Supported events:
- Workflow started
- Skill started/completed
- Provider request
- Tool call
- Workspace read
- Memory lookup
- RAG lookup
- Blueprint generated
- Context compression
- Error
- Verification
- Release

For every event record:
- Timestamp
- Workflow checkpoint
- Skill
- Request ID (if applicable)
- Active context
- Context delta
- Input / Output tokens
- Cost
- Duration

Timeline Visualization:
Implement an interactive timeline showing:
- Context growth
- Cost growth
- Token growth
- Skill markers
- Checkpoints
- Context spikes
- Errors
- Context resets
Users can zoom, filter, and click any event to inspect details.

Predictive Analytics:
Estimate:
- Remaining context before limit
- Predicted context after next request
- Estimated requests remaining
- Estimated cost to complete workflow
- Context exhaustion probability
Display confidence levels.

Dashboard:
Add a dedicated Timeline page including:
- Interactive charts
- Event markers
- Context trend
- Cost trend
- Prediction panel
- Forecast warnings

CLI:
Provide timeline/report commands:
- timeline
- forecast
- trend
- predict
Adapt command names to the current AIWF CLI.

Database:
Persist:
- Timeline events
- Forecast snapshots
- Trend history
Maintain backward compatibility.

Automated Tests:
Verify:
- Timeline ordering
- Event correlation
- Forecast accuracy
- Trend calculations
- Dashboard rendering
- SQLite persistence

## 3. Business Problem
- **Problem**: Người dùng gặp khó khăn trong việc theo dõi diễn biến hoạt động của workflow theo thời gian thực và không biết trước khi nào context sẽ đạt ngưỡng quá tải, dẫn đến việc đột ngột gián đoạn công việc hoặc chi phí vượt mức kiểm soát.
- **Why it matters**: Nâng cao năng lực chẩn đoán trực quan của AIWF, dự báo chính xác thời điểm cạn kiệt tài nguyên giúp tiết kiệm thời gian và tài chính.
- **Who is affected**: Lập trình viên và các kiến trúc sư AI vận hành hệ thống AIWF.
- **Expected outcome**: Cung cấp đồ thị thời gian tích hợp bộ máy dự báo chuyên nghiệp.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Ghi nhận 12 loại sự kiện trong vòng đời hệ thống vào SQLite.
  - FR-02: Bộ phân tích dự báo (Predictive Engine) tính toán dung lượng context của request tiếp theo, xác suất cạn kiệt ngữ cảnh và dự toán số request còn lại.
  - FR-03: Hiển thị tab Timeline trực quan sinh động tích hợp biểu đồ Sparkline/Growth trend, cảnh báo dự phòng.
  - FR-04: CLI hỗ trợ tra cứu lịch sử sự kiện và dự báo nhanh.
- **Non-functional Requirements**:
  - NFR-01: Heuristic dự báo nhanh gọn, tin cậy, không làm chậm tốc độ thực thi dòng lệnh.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Việc tính toán dự đoán (Predictive Analytics) có sử dụng mô hình học máy (Machine Learning) phức tạp không? | Không, để đảm bảo tốc độ và tính tin cậy, chúng ta sẽ áp dụng các thuật toán hồi quy tuyến tính (Linear Regression) đơn giản và các hệ số trượt (moving average) dựa trên lịch sử request của session hiện tại. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Solution Options Evaluated

### Option A: Timeline Engine + SQLite Persistence + Predictive Tab (Khuyên dùng)
- **Overview**:
  - Thiết kế bảng SQLite `timeline_events` ghi nhận chi tiết 12 loại sự kiện.
  - Viết module `forecaster.py` chịu trách nhiệm chạy hồi quy xu hướng tăng trưởng context và cost.
  - CLI mở rộng `usage timeline` và `usage forecast`.
  - Tích hợp tab **Timeline Dashboard** trong Visualizer Webview.
- **Advantages**: Khả năng theo dõi chi tiết mọi sự kiện, dữ liệu lưu trữ ổn định bền vững, thuật toán dự đoán độc lập dễ viết unit test.
- **Complexity**: Medium
- **Risk**: Low

### Option B: Vẽ Timeline thời gian thực bằng JS trên Webview mà không lưu database
- **Disadvantages**: Không có dữ liệu của các sự kiện không tạo LLM request, dự toán dự báo không lưu trữ được lịch sử.

## 8. Selected Solution
- **Choice**: Option A — Timeline Engine + SQLite Persistence + Predictive Tab

## 9. Acceptance Criteria
- [ ] Sự kiện ghi nhận đúng loại, đầy đủ tham số và thứ tự thời gian trong SQLite.
- [ ] Công thức dự báo đưa ra xác suất cạn kiệt ngữ cảnh chính xác dựa trên ngưỡng 2.0M tokens.
- [ ] Giao diện Timeline vẽ đồ thị trực quan, hỗ trợ zoom/filter sự kiện.
