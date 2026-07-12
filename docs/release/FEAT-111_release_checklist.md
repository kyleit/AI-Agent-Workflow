# Release Checklist — FEAT-111

Bảng kiểm chứng các tiêu chí phát hành cho Hierarchical Multi-Agent Runtime.

## 1. Runtime Readiness
- [x] Không còn tác nhân chạy ngầm (No running workers remain).
- [x] Không còn khoá tranh chấp (No active locks remain).
- [x] Không còn điểm checkpoint đang chờ xử lý (No active checkpoints remain).
- [x] Hồ sơ uỷ quyền `authorization.json` đã được gắn cờ hết hạn (`authorization_status = expired`).
- [x] Loại bỏ hoàn toàn dấu vết và tệp tin `.agents/.session.json`.

## 2. Code & Tests Integrity
- [x] Chạy biên dịch TypeScript Visualizer: **PASS**.
- [x] Đồng bộ webviewHtml: **PASS**.
- [x] Chạy unit tests: **PASS** (100% test cases thành công).
