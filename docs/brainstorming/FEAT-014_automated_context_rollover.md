<!-- File path: docs/brainstorming/FEAT-014_automated_context_rollover.md -->

---
artifact_type: brainstorm
feature_id: FEAT-014
feature_name: Automated Context Rollover & Recovery
status: active
---

# Feature Brainstorming – Automated Context Rollover & Recovery (FEAT-014)

## 1. Bối cảnh & Vấn đề
Khi AI Coding Agent thực hiện các cuộc hội thoại dài để phát triển phần mềm, lượng token tiêu thụ tăng dần lên đến giới hạn của mô hình (ví dụ: 2M tokens). Việc này gây ra:
- Phản hồi chậm, chi phí API tăng cao.
- Tràn context gây lỗi giữa chừng.
- Hiện tại, người dùng phải tự mở chat mới và gõ lệnh `/resume-workflow` bằng tay để khôi phục.

## 2. Mục tiêu
Tự động hóa hoàn toàn việc giám sát, cảnh báo và khôi phục bối cảnh làm việc khi context của cuộc hội thoại sắp cạn kiệt, giúp nhà phát triển chuyển đổi sang phiên trò chuyện mới mượt mà nhất.

## 3. Đề xuất Giải pháp Kỹ thuật

### A. Cơ chế Giám Sát Tự Động (Warning Gate)
- Tích hợp logic kiểm tra `context_usage` trong CLI `workflow_runtime.py` (ở các lệnh `validate`, `step`, `complete`, `heartbeat`).
- Khi lượng token sử dụng đạt $\ge 85\%$, CLI in cảnh báo đỏ nổi bật trên Terminal:
  > `⚠️ [SYSTEM WARNING]: Context limit is at 85% (1.7M / 2.0M tokens). To prevent slowdowns, please restart the chat session. Run '/workflow reset' to rollover safely.`

### B. Cơ chế Đóng Gói Bối Cảnh (Context Snapshotting)
- CLI bổ sung subcommand mới: `python3 workflow_runtime.py compact` (hoặc `rollover`).
- Lệnh này sẽ tạo ra tệp tin nhỏ gọn `.agents/runtime/context_snapshot.json` lưu giữ thông tin bối cảnh:
  ```json
  {
    "checkpoint": 3,
    "current_skill": "brainstorming",
    "current_command": "brainstorm",
    "current_step": "Requirement Discovery Completed",
    "active_feature_id": "FEAT-014",
    "git_diff_summary": {
      "modified_files": ["docs/brainstorming/FEAT-014_automated_context_rollover.md"],
      "untracked_files": []
    },
    "rollover_requested_at": "2026-07-07T10:35:00+07:00"
  }
  ```

### C. Cơ chế Tự Phục Hồi (Auto-Resume)
- Khi Agent mới khởi động (trong Thread mới), hành động đầu tiên trong `initialize-workflow` hoặc `resume-workflow` là quét tìm tệp `.agents/runtime/context_snapshot.json`.
- Nếu tệp tồn tại:
  1. Agent tự động nạp trạng thái, khôi phục bối cảnh làm việc.
  2. Xóa hoặc đổi tên tệp snapshot sau khi khôi phục thành công để tránh lặp lại.
  3. In ra lời chào thông báo cho người dùng biết bối cảnh đã được khôi phục thành công.

## 4. Câu hỏi thảo luận / Open Questions
1. **IDE UI Integration**: IDE có thể cung cấp nút bấm hoặc popup tự động kích hoạt tạo Thread mới khi CLI báo động đỏ không?
2. **Git Auto-Stash**: Nếu người dùng đang có các tệp tin sửa đổi chưa commit, việc rollover có nên tự động gọi `git stash` để bảo vệ mã nguồn, rồi khôi phục lại ở Thread mới không? (Khuyên dùng: có, giúp chuyển đổi an toàn 100%).
