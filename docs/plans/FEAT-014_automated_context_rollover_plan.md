<!-- File path: docs/plans/FEAT-014_automated_context_rollover_plan.md -->

---
feature_id: FEAT-014
feature_name: Automated Context Rollover & Recovery
status: reviewed
stage: planning
created_at: 2026-07-07
updated_at: 2026-07-07
previous_artifact: ../brainstorming/FEAT-014_automated_context_rollover.md
next_artifact: ../designs/FEAT-014_automated_context_rollover_blueprint.md
---

# FEAT-014: Automated Context Rollover & Recovery

## Objective
- **Mục tiêu**: Tự động hóa quá trình rollover (reset) context trò chuyện khi số lượng token tiêu thụ đạt ngưỡng giới hạn an toàn ($\ge 85\%$).
- **Kết quả mong đợi**: Giúp nhà phát triển chuyển đổi mượt mà sang Thread mới mà không cần thao tác thủ công, đồng thời tự động khôi phục hoàn toàn bối cảnh làm việc và trạng thái Git chưa commit.

## Scope
### Included
- Thiết lập cơ chế cảnh báo tự động trên CLI khi `context_usage` vượt quá 85%.
- Xây dựng lệnh CLI đóng gói bối cảnh (`compact` hoặc `rollover`) để xuất tệp trạng thái `.agents/runtime/context_snapshot.json`.
- Thiết lập logic tự động quét và khôi phục bối cảnh trò chuyện (Auto-Resume) khi Agent bắt đầu phiên trò chuyện mới.
- Cơ chế Git Auto-Stash và Auto-Stash Pop tự động khi chuyển đổi Thread nhằm bảo vệ mã nguồn chưa commit.

### Excluded
- Giao diện đồ họa (UI Webview) để người dùng click chuyển đổi (chỉ tập trung vào CLI và prompt hướng dẫn của Agent).
- Thay đổi cấu hình token của mô hình LLM từ xa (chỉ xử lý cục bộ trên máy trạm thông qua session).

## Project Impact
- **Modules**: `workflow-runtime`, `initialize-workflow`, `resume-workflow`.
- **Config**: Bổ sung cấu hình ngưỡng rollover trong session schema.

## Dependencies
- central CLI Engine: Cần hoạt động chính xác với cơ chế ghi/đọc tệp cấu hình session đã sửa ở FIX-010.

## Risks
- **Trùng lặp khôi phục**: Tệp snapshot có thể bị đọc nhiều lần nếu không được xóa kịp thời $\rightarrow$ *Mitigation*: Xóa hoặc đổi tên tệp snapshot ngay lập tức sau khi khôi phục thành công.
- **Xung đột Git Stash**: Lệnh `git stash pop` có thể gặp conflict nếu code bị sửa đổi ngoài luồng $\rightarrow$ *Mitigation*: Ghi log cảnh báo rõ ràng cho người dùng tự xử lý nếu có conflict.

## Acceptance Criteria
- CLI in cảnh báo đỏ nổi bật khi `context_usage` đạt $\ge 85\%$.
- Lệnh tạo snapshot hoạt động chính xác, tạo ra file `.json` chứa đủ thông tin bối cảnh SDLC.
- Agent ở Thread mới phát hiện được snapshot, khôi phục bối cảnh thành công và tự động dọn dẹp tệp snapshot cũ.
- Tự động stash/unstash code an toàn mà không làm mất mát mã nguồn chưa commit.

## Deliverables
- Tệp đặc tả kế hoạch triển khai `docs/plans/FEAT-014_automated_context_rollover_plan.md`.
- Kịch bản CLI cập nhật và logic tích hợp trong các Skill liên quan.

## Estimated Complexity
- **Medium**: Đòi hỏi phối hợp đồng bộ giữa CLI Python và prompt hướng dẫn khôi phục của Agent ở Thread mới.

## Recommended Blueprint Focus
- **Thiết kế**: Tập trung vào cấu trúc dữ liệu của tệp snapshot `context_snapshot.json` để đảm bảo lưu trữ gọn nhẹ nhất, và luồng tuần tự (sequence flow) của việc stash/unstash git.

## Recommended Next Skill
/blueprint
