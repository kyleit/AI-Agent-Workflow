<!-- File path: docs/plans/FEAT-039_smart_context_rebuilder_plan.md -->

---
feature_id: FEAT-039
feature_name: Smart Context Rebuilder
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-039_smart_context_rebuilder.md
next_artifact: ../designs/FEAT-039_smart_context_rebuilder_blueprint.md
---

# FEAT-039: Smart Context Rebuilder

## Objective
- **Business Objective**: Ráp ngữ cảnh tối thiểu một cách thông minh (Context Bundle) trước khi gửi request tới nhà cung cấp LLM, thay thế việc gửi lại toàn bộ hội thoại cũ lãng phí.
- **Expected Outcome**:
  - Tự động nén, lược bỏ trùng lặp và tổng hợp ngữ cảnh dựa trên cache mã băm SHA256.
  - Cắt giảm dung lượng tokens hội thoại tối thiểu 80%.
  - Cung cấp Tab Smart Context Rebuilder trực quan trên Webview Dashboard.
  - CLI hỗ trợ các lệnh `usage context`.

## Scope

### Included
- Thiết kế bảng SQLite `context_bundles`, `cache_metadata` và `rebuild_history`.
- Phát triển module `context_rebuilder.py` quản lý thuật toán ráp và cache.
- Tích hợp hook tiền xử lý trước mỗi LLM request.
- Tab hiển thị Smart Context Rebuilder trên Dashboard.

### Excluded
- Không hỗ trợ tự động xóa mã nguồn hoặc các thay đổi lớn mà không được người dùng cấu hình an toàn.

## Project Impact
- **Database**: Thêm các bảng SQLite quản lý cache và lịch sử ráp.
- **CLI**: Mở rộng các subcommands dòng lệnh của `workflow_runtime.py`.
- **Webview**: Thêm tab Smart Context và các cấu phần giao diện.

## Dependencies
- Dữ liệu lịch sử request từ `provider_requests`.

## Risks
- **Risk**: Thiếu thông tin ngữ cảnh quan trọng do thuật toán tối giản quá đà.
  - **Mitigation**: Luôn luôn giữ nguyên 100% nội dung của tệp `AI_RULES.md`, các tệp đang có thay đổi chưa commit (`git diff`), và các chỉ dẫn trực tiếp của người dùng.

## Acceptance Criteria
- [ ] Giảm tối thiểu 80% tokens hội thoại đầu vào trên các phiên làm việc dài hạn.
- [ ] Cache tự động invalidate khi tệp nguồn thay đổi mã băm SHA256.
- [ ] Giao diện hiển thị đúng các nguồn Include/Skip và dung lượng tiết kiệm.

## Deliverables
- Module `context_rebuilder.py`.
- Bổ sung cấu trúc SQLite schema di trú trong `db.py`.
- Tích hợp CLI trong `workflow_runtime.py`.
- Bổ sung Tab Smart Context trong `webview.html` & `extension.ts`.

## Estimated Complexity
- **High**: Đòi hỏi logic tổng hợp mã băm và tóm tắt tệp tin cực kỳ chính xác.
