<!-- File path: docs/plans/FEAT-032_context_breakdown_plan.md -->

---
feature_id: FEAT-032
feature_name: Phase 1 - Context Breakdown
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorm/FEAT-032_context_breakdown.md
next_artifact: ../designs/FEAT-032_context_breakdown_blueprint.md
---

# FEAT-032: Phase 1 - Context Breakdown

## Objective
- Xây dựng Context Breakdown Engine nhằm phân tích chi tiết lượng token đóng góp của từng tài nguyên trong active context của lượt prompt cuối cùng.
- Hiển thị Tree view trực quan kèm theo progress bar dưới Visualizer sidebar panel của VS Code giúp nhà phát triển nắm được chi phí phân bổ context.

## Scope
### Included
- Tạo module `breakdown_engine.py` thực hiện quét transcript và bóc tách các thẻ XML cứu cánh.
- Ghi nhận và phân loại context thành các nhóm chính: *AI_RULES, AGENTS, Loaded Skills, History, User Prompt, Workspace Reads, Project Memory, RAG, Tool Results, Logs, Other*.
- Thêm lệnh Diagnostics in bảng báo cáo dưới terminal: `aiwf usage breakdown`.
- Thiết kế Tree view, Progress bar và Highlighting nguồn lớn nhất dưới webview visualizer.
- Bộ kiểm thử tự động.

### Excluded
- Không tối ưu hóa hay nén tự động lượng token trong pha này (chỉ đo lường phân bổ).
- Không chạy logic phân tích hay tính toán token trong webview (chỉ hiển thị dữ liệu thô nhận từ backend).

## Project Impact
- **Modules**: Thêm mới `breakdown_engine.py` trong `workflow-runtime`.
- **UI**: Thêm panel mới `#context-breakdown-panel` hiển thị Tree view dưới Footer của Visualizer.
- **Config & State**: Thêm tệp trạng thái mới `.agents/state/breakdown.json`.

## Dependencies
- Phụ thuộc vào cấu trúc tệp transcript (`transcript.jsonl`) được tự động cập nhật bởi IDE và Split State Manager.

## Risks
- **Rủi ro**: Parsing tệp log transcript quá lớn làm suy giảm hiệu suất.
- **Biện pháp**: Chỉ đọc và phân tích lượt tương tác (turn) cuối cùng của transcript để lấy active context.

## Acceptance Criteria
- Phân tích chính xác dung lượng token của các nguồn context.
- Kết quả được xuất ra `.agents/state/breakdown.json`.
- Giao diện Visualizer hiển thị Tree view tương tác, progress bar và highlight nguồn lớn nhất.
- Unit test chạy thành công bao phủ các kịch bản context lớn, nhỏ, nhiều skills.

## Deliverables
- `skills/workflow-runtime/scripts/breakdown_engine.py`
- Giao diện Visualizer Tree view (`webview.html`)
- Bộ automated unit tests (`test_breakdown.py`)
- Tài liệu nghiệm thu (`walkthrough.md`)

## Estimated Complexity
- Medium. Yêu cầu bóc tách văn bản chuẩn xác và cấu trúc Tree view trực quan dưới webview.

## Recommended Blueprint Focus
- Tập trung thiết kế thuật toán phân tách chuỗi transcript dựa trên regex các tag XML biên giới của tài nguyên và cấu trúc CSS hiển thị Tree view linh hoạt dưới HTML.

## Recommended Next Skill
/blueprint
