<!-- File path: docs/plans/FEAT-036_runtime_insights_advisor_plan.md -->

---
feature_id: FEAT-036
feature_name: Runtime Insights & Optimization Advisor
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-036_runtime_insights_advisor.md
next_artifact: ../designs/FEAT-036_runtime_insights_advisor_blueprint.md
---

# FEAT-036: Runtime Insights & Optimization Advisor

## Objective
- **Business Objective**: Giúp nhà phát triển phân tích sâu chi phí và tối ưu hóa runtime context thông qua các đề xuất tự động (Optimization Advisor) và trang dashboard trực quan sinh động.
- **Expected Outcome**:
  - Module Heuristic Python phát hiện các vấn đề lặp dữ liệu, phình to context.
  - Lưu snapshot phân tích và trạng thái Accept/Ignore vào SQLite.
  - CLI hỗ trợ các lệnh kiểm toán chỉ số.
  - Bảng điều khiển Insights chuyên sâu tích hợp trên visualizer extension.

## Scope

### Included
- Viết module Python `insights_engine.py` thực hiện các Heuristics đề xuất và chấm điểm hiệu năng.
- Di trú database SQLite thêm hai bảng: `insight_snapshots` và `recommendations`.
- CLI tích hợp lệnh `usage insights` và `usage optimize`.
- Thiết kế Dashboard Runtime Insights trên Visualizer Webview.
- Ghi nhận và đồng bộ tự động trạng thái tối ưu hóa.

### Excluded
- Không tự động thực thi dọn dẹp các tệp tin vật lý của workspace (chỉ đưa ra đề xuất để người dùng xác nhận thủ công).

## Project Impact
- **Database Schema**: Thêm 2 bảng SQLite mới.
- **CLI Commands**: Mở rộng Parser dòng lệnh.
- **Webview UI**: Thiết kế thêm trang Dashboard tab và các card hiển thị.

## Dependencies
- Dữ liệu lịch sử request và diff từ Phase 2 & 3.

## Risks
- **Risk**: Đề xuất không chính xác hoặc tính sai lượng token tiết kiệm dự kiến.
  - **Mitigation**: Áp dụng các ngưỡng tỷ lệ tối thiểu (ví dụ: chỉ đề xuất nén khi Conversation History chiếm > 50% context).

## Acceptance Criteria
- [ ] Tính toán đúng Efficiency Score, xu hướng tăng trưởng và dự toán tiết kiệm.
- [ ] Chấp nhận (Accept) tối ưu qua CLI cập nhật đúng trạng thái trong SQLite.
- [ ] Hiển thị chính xác các thẻ đề xuất trên giao diện Webview.

## Deliverables
- Module `insights_engine.py`.
- Tích hợp database SQLite di trú trong `db.py`.
- Sửa đổi CLI `workflow_runtime.py`.
- Sửa đổi UI Webview `webview.html` & `extension.ts`.

## Estimated Complexity
- **Medium**: Cần phối hợp xử lý thuật toán tối ưu hóa, lưu trữ dữ liệu và vẽ giao diện UI.

## Recommended Blueprint Focus
- Tập trung vào thiết kế thuật toán Heuristic chẩn đoán và cấu trúc bảng SQLite lưu trữ lịch sử đề xuất.

## Recommended Next Skill
/blueprint
