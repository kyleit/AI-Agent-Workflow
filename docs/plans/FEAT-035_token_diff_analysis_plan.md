<!-- File path: docs/plans/FEAT-035_token_diff_analysis_plan.md -->

---
feature_id: FEAT-035
feature_name: Token Diff Analysis
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-035_token_diff_analysis.md
next_artifact: ../designs/FEAT-035_token_diff_analysis_blueprint.md
---

# FEAT-035: Token Diff Analysis

## Objective
- **Business Objective**: Cho phép người dùng kiểm toán, so sánh sự thay đổi lượng token trong active context giữa các bước (requests) trong cùng hội thoại để tối ưu chi phí LLM.
- **Expected Outcome**: Cung cấp giao diện bảng sai biệt (Token Diff panel) hiển thị Thêm/Bớt/Thay đổi ròng và tỷ lệ % theo 15 danh mục, hỗ trợ CLI truy vấn diff và tích hợp chọn 2 request bất kỳ từ timeline.

## Scope

### Included
- Viết module toán học Diff Engine ở Backend Python.
- Tạo bảng SQLite di trú `token_diffs` để lưu trữ diff giữa 2 bước kế tiếp nhau.
- Bổ sung lệnh CLI `usage diff <req_a> <req_b>` và API lấy dữ liệu diff.
- Tạo giao diện hiển thị Token Diff trên Visualizer Webview (Waterfall/Delta chart + so sánh Timeline).

### Excluded
- Không tự động dọn dẹp (auto-purge) dữ liệu lịch sử diff trong phase này.
- Không so sánh giữa 2 hội thoại khác nhau.

## Project Impact
- **Database Schema**: Thêm bảng di trú `token_diffs` và indexes hỗ trợ.
- **CLI Commands**: Mở rộng Parser của `workflow_runtime.py` hỗ trợ các truy vấn so sánh.
- **UI Webview**: Thiết kế khu vực Token Diff Panel hiển thị đồ thị và thông tin chi tiết.

## Dependencies
- Bảng dữ liệu `provider_requests` có chứa context breakdown json đầy đủ từ Phase 2.

## Risks
- **Risk**: Phình to dung lượng SQLite do lưu trữ lịch sử.
  - **Mitigation**: Chỉ lưu trữ các diff kế tiếp liền kề (N vs N-1), không lưu tích lũy chéo. So sánh ngẫu nhiên (A vs B) được tính toán động (on-demand) từ Extension Host.

## Acceptance Criteria
- [ ] Tính toán chính xác sai biệt từng danh mục.
- [ ] Cho phép chọn 2 request bất kỳ để so sánh trên giao diện và trả về JSON chuẩn xác.

## Deliverables
- Tệp tin di trú cơ sở dữ liệu `migrate_diff.py` (nếu cần) hoặc nâng cấp tự động tại `db.py`.
- Module Backend Python `diff_engine.py`.
- Sửa đổi CLI `workflow_runtime.py`.
- Sửa đổi UI Webview `webview.html`.

## Estimated Complexity
- **Medium**: Cần phối hợp xử lý toán học backend và thiết kế UI mượt mà ở frontend.

## Recommended Blueprint Focus
- Tập trung thiết kế thuật toán so sánh Breakdown JSON và đặc tả giao diện bảng Diff trên Webview.

## Recommended Next Skill
/blueprint
